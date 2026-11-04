import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;

/** H10 tests actual Java ProcessBuilder -> Python subprocess and stale-request gate. */
public final class H10JavaRegression {
    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
    private static ProcessBuilder python(String executable, String code) {
        return new ProcessBuilder(executable, "-c", code);
    }
    private static ProcessBuilder request(String executable, boolean knownColor) {
        List<String> command = new ArrayList<>(List.of(executable, "-m", "shopping_decision.desktop_bridge"));
        String[] fields = {"printer test", "200", "", "", knownColor ? "false" : "", "", "", "", ""};
        for (String field : fields) {
            command.add(Base64.getEncoder().encodeToString(field.getBytes(StandardCharsets.UTF_8)));
        }
        return new ProcessBuilder(command);
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("Usage: H10JavaRegression <python>");
        String py = args[0];
        Map<String, String> normal = DesktopBridgeClient.invoke(request(py, true), 10_000);
        check("defer".equals(normal.get("status")), "known-color normal request should defer");
        check(normal.getOrDefault("report_json", "").length() > 1000, "missing full audit record");
        System.out.println("PASS known-color real backend; full audit chars=" + normal.get("report_json").length());

        Map<String, String> clarify = DesktopBridgeClient.invoke(request(py, false), 10_000);
        check("clarify".equals(clarify.get("status")), "unknown color should clarify");
        System.out.println("PASS short real backend clarification");

        String big = "import base64; print('status\\t'+base64.b64encode(b'X'*131072).decode())";
        Map<String, String> large = DesktopBridgeClient.invoke(python(py, big), 10_000);
        check(large.get("status").length() == 131072, "128KiB output was not fully consumed");
        System.out.println("PASS 128KiB output drained");

        try {
            DesktopBridgeClient.invoke(python(py, "import sys; print('oops'); sys.exit(17)"), 10_000);
            throw new AssertionError("nonzero exit unexpectedly accepted");
        } catch (IOException expected) {
            check(expected.getMessage().contains("17"), "exit-code diagnostics lost");
            System.out.println("PASS nonzero exit");
        }

        try {
            DesktopBridgeClient.invoke(python(py, "import time; time.sleep(3)"), 250);
            throw new AssertionError("hanging process did not time out");
        } catch (IOException expected) {
            check(expected.getMessage().contains("超过"), "timeout diagnostics lost");
            System.out.println("PASS real timeout and cleanup");
        }

        DesktopRequestGate gate = new DesktopRequestGate();
        long originalVersion = gate.next();
        ExecutorService threads = Executors.newSingleThreadExecutor();
        try {
            ProcessBuilder delayed = request(py, true);
            delayed.environment().put("SHOPPING_H09_TEST_DELAY_MS", "750");
            Future<Map<String, String>> stale = threads.submit(() -> DesktopBridgeClient.invoke(delayed, 10_000));
            Thread.sleep(100);
            gate.invalidate();
            long newVersion = gate.next();
            Map<String, String> fresh = DesktopBridgeClient.invoke(request(py, false), 10_000);
            check("clarify".equals(fresh.get("status")), "new conditions not reflected");
            check(gate.accepts(newVersion), "new request rejected");
            check("defer".equals(stale.get(10, TimeUnit.SECONDS).get("status")), "old process did not finish");
            check(!gate.accepts(originalVersion), "old result could override newer snapshot");
            System.out.println("PASS changed conditions invalidate delayed old result");
        } finally {
            threads.shutdownNow();
        }
        System.out.println("H10 Java subprocess regression: 6/6 PASS");
    }
}
