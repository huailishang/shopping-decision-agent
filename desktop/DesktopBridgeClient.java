import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;

/** H10: consume child stdout concurrently with waiting; no network or transaction calls. */
final class DesktopBridgeClient {
    static final int MAX_OUTPUT_BYTES = 2 * 1024 * 1024;
    private DesktopBridgeClient() {}

    static Map<String, String> invoke(ProcessBuilder builder, long timeoutMillis)
            throws IOException, InterruptedException {
        if (timeoutMillis <= 0) throw new IllegalArgumentException("timeoutMillis must be positive");
        Process process = builder.redirectErrorStream(true).start();
        Drain drain = new Drain(process.getInputStream());
        Thread reader = new Thread(drain, "shopping-output-drain");
        reader.setDaemon(true);
        reader.start(); // Drain BEFORE waitFor; otherwise large report_json blocks the subprocess.
        try {
            if (!process.waitFor(timeoutMillis, TimeUnit.MILLISECONDS)) {
                throw new IOException("后端超过" + timeoutMillis + "毫秒未响应");
            }
            reader.join(2000);
            if (reader.isAlive()) throw new IOException("后端已结束，但输出读取尚未完成");
            if (drain.error != null) throw drain.error;
            if (drain.overflow) throw new IOException("后端输出超过2MiB安全上限");
            String raw = new String(drain.bytes(), StandardCharsets.UTF_8);
            if (process.exitValue() != 0) {
                throw new IOException("后端异常退出(" + process.exitValue() + "): " + abbreviated(raw));
            }
            Map<String, String> values = new LinkedHashMap<>();
            for (String line : raw.split("\\R")) {
                int tab = line.indexOf('\t');
                if (tab <= 0) continue;
                try {
                    byte[] decoded = Base64.getDecoder().decode(line.substring(tab + 1));
                    values.put(line.substring(0, tab), new String(decoded, StandardCharsets.UTF_8));
                } catch (IllegalArgumentException bad) {
                    throw new IOException("后端输出编码无效", bad);
                }
            }
            if (!values.containsKey("status") && !values.containsKey("error")) {
                throw new IOException("后端没有返回有效决策状态: " + abbreviated(raw));
            }
            return values;
        } finally {
            if (process.isAlive()) process.destroyForcibly();
            try { process.waitFor(2, TimeUnit.SECONDS); }
            catch (InterruptedException ex) { Thread.currentThread().interrupt(); }
            try { process.getInputStream().close(); }
            catch (IOException ignored) {}
            reader.interrupt();
            try { reader.join(1000); }
            catch (InterruptedException ex) { Thread.currentThread().interrupt(); }
        }
    }

    private static String abbreviated(String text) {
        return text.length() <= 280 ? text : text.substring(0, 280) + "…";
    }

    private static final class Drain implements Runnable {
        private final InputStream stream;
        private final ByteArrayOutputStream data = new ByteArrayOutputStream();
        volatile IOException error;
        volatile boolean overflow;
        Drain(InputStream stream) { this.stream = stream; }
        byte[] bytes() { return data.toByteArray(); }
        @Override public void run() {
            try (InputStream input = stream) {
                byte[] chunk = new byte[8192];
                int n;
                while ((n = input.read(chunk)) != -1) {
                    int remaining = MAX_OUTPUT_BYTES - data.size();
                    if (n > remaining) overflow = true;
                    if (remaining > 0) data.write(chunk, 0, Math.min(n, remaining));
                    // Continue draining overflow without storing to prevent pipe deadlock.
                }
            } catch (IOException ex) { error = ex; }
        }
    }
}

/** Version gate shared by Swing UI and headless Java regression tests. */
final class DesktopRequestGate {
    private long current;
    synchronized long next() { return ++current; }
    synchronized void invalidate() { current++; }
    synchronized boolean accepts(long version) { return version == current; }
}
