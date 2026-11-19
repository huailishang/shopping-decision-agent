import javax.swing.*;
import java.awt.GraphicsEnvironment;
import java.lang.reflect.*;
import java.util.concurrent.atomic.AtomicReference;

/** 有显示环境时实际构造Swing窗口，点击参考、发送及修改；不触发商城或保存。 */
public final class ChatSwingRegression {
    private static Object field(Object obj, String name) throws Exception {
        Field f = obj.getClass().getDeclaredField(name); f.setAccessible(true); return f.get(obj);
    }
    private static void check(boolean ok, String msg) {
        if (!ok) throw new AssertionError(msg);
    }
    private static void ui(Runnable work) throws Exception { SwingUtilities.invokeAndWait(work); }
    private static void until(Object app, String expected) throws Exception {
        for (int i=0; i<90; i++) {
            AtomicReference<String> read=new AtomicReference<>("");
            ui(() -> { try {read.set((String)field(app, "chatState")); } catch(Exception ex) {throw new RuntimeException(ex);} });
            if (read.get().contains(expected)) return;
            Thread.sleep(100);
        }
        throw new AssertionError("Swing backend no response within bounded local check");
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("Usage: ChatSwingRegression python3");
        if (GraphicsEnvironment.isHeadless()) {
            System.out.println("SKIP native Swing display: headless environment");
            return;
        }
        AtomicReference<Object> owner = new AtomicReference<>();
        try {
            ui(() -> {
                try {
                    Constructor<ShoppingDecisionDesktop> ctor=ShoppingDecisionDesktop.class.getDeclaredConstructor(String.class);
                    ctor.setAccessible(true);
                    owner.set(ctor.newInstance(args[0]));
                } catch(Exception ex) {throw new RuntimeException(ex);}
            });
        } catch (java.awt.AWTError noDisplay) {
            if (noDisplay.getMessage() != null && noDisplay.getMessage().contains("X11")) {
                System.out.println("SKIP native Swing display: X11 server not reachable");
                return;
            }
            throw noDisplay;
        }
        Object app=owner.get();
        try {
            until(app, "\"version\": 0");
            ui(() -> {
                try {
                    JPanel buttons=(JPanel)field(app, "chatReferences");
                    JTextArea input=(JTextArea)field(app, "chatInput");
                    check(buttons.getComponentCount()>0, "reference buttons absent");
                    JButton ref=null;
                    for (java.awt.Component c:buttons.getComponents())
                        if (c instanceof JButton b && "打印机".equals(b.getText())) ref=b;
                    check(ref!=null,"printer reference absent");
                    ref.doClick();
                    check("打印机".equals(input.getText()), "reference did not populate draft");
                    check(((String)field(app, "chatState")).contains("\"version\": 0"),
                          "clicked draft incorrectly confirmed");
                    ((JButton)field(app,"chatSend")).doClick();
                } catch(Exception ex) {throw new RuntimeException(ex);}
            });
            until(app, "\"category\": {");
            ui(() -> {
                try {
                    JTextArea input=(JTextArea)field(app,"chatInput");
                    input.setText("家用打印，希望微信打印");
                    ((JButton)field(app,"chatSend")).doClick();
                } catch(Exception ex) {throw new RuntimeException(ex);}
            });
            until(app, "\"usage\": {");
            ui(() -> {
                try {
                    check(!((JTextArea)field(app,"chatOutcome")).getText().isBlank(), "result view empty");
                    check(((String)field(app,"chatReport")).contains("\"transactions_enabled\": false"),"no transaction guard");
                    System.out.println("PASS actual Swing construct/reference draft/send/usage/result version");
                } catch(Exception ex) {throw new RuntimeException(ex);}
            });
        } finally {
            ui(() -> { try {((JFrame)field(app,"frame")).dispose();} catch(Exception ignored) {} });
        }
    }
}
