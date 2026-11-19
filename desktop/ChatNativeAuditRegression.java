import javax.swing.*;
import java.awt.*;
import java.io.File;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.atomic.AtomicReference;

/**
 * 真实可见 Swing 窗口与系统模态对话框的执行者回归。
 * 不是人工/独立验收；仅在可用显示服务下执行。拒绝无显示时伪造保存成功。
 * 参数: python3 reports/chat_native_audit_20261116_run01.txt
 */
public final class ChatNativeAuditRegression {
    private static Object field(Object obj, String name) throws Exception {
        Field f = obj.getClass().getDeclaredField(name);
        f.setAccessible(true);
        return f.get(obj);
    }
    private static void check(boolean condition, String why) {
        if (!condition) throw new AssertionError(why);
    }
    private static void ui(Runnable work) throws Exception {
        SwingUtilities.invokeAndWait(work);
    }
    private static <T> T read(Checked<T> task) throws Exception {
        AtomicReference<T> value = new AtomicReference<>();
        AtomicReference<Exception> error = new AtomicReference<>();
        ui(() -> {try {value.set(task.run());} catch(Exception e) {error.set(e);}});
        if (error.get() != null) throw error.get();
        return value.get();
    }
    private interface Checked<T> { T run() throws Exception; }
    private static void until(String name, Checked<Boolean> condition) throws Exception {
        for (int i = 0; i < 180; i++) {
            if (read(condition)) return;
            Thread.sleep(100);
        }
        throw new AssertionError("timed out waiting for " + name);
    }
    private static JButton button(Container parent, String label) {
        for (Component c : parent.getComponents()) {
            if (c instanceof JButton b && label.equals(b.getText())) return b;
            if (c instanceof Container child) {
                JButton nested = button(child, label);
                if (nested != null) return nested;
            }
        }
        return null;
    }
    private static void click(Container parent, String label) {
        JButton b=button(parent,label);
        check(b != null, "button not found: " + label);
        b.doClick();
    }
    private static JDialog visibleDialog(String titleContains) {
        for (Window w : Window.getWindows()) {
            if (w instanceof JDialog d && d.isVisible() && d.getTitle().contains(titleContains))
                return d;
        }
        return null;
    }
    private static void answer(Object app, String fieldLabel, String answer) throws Exception {
        ui(() -> {
            try {
                click((JPanel)field(app, "chatEdits"), fieldLabel);
                ((JTextArea)field(app,"chatInput")).setText(answer);
                ((JButton)field(app,"chatSend")).doClick();
            } catch (Exception e) {throw new RuntimeException(e);}
        });
    }
    private static int version(Object app) throws Exception {
        String state=read(() -> (String)field(app,"chatState"));
        java.util.regex.Matcher m=java.util.regex.Pattern.compile("\\\"version\\\"\\s*:\\s*(\\d+)").matcher(state);
        check(m.find(),"no chat version");
        return Integer.parseInt(m.group(1));
    }
    private static void waitVersion(Object app, int wanted) throws Exception {
        until("version " + wanted, () -> {
            String s=(String)field(app,"chatState");
            return s.contains("\"version\": " + wanted) && ((JButton)field(app,"chatSend")).isEnabled();
        });
    }
    private static JFileChooser fileChooser(JDialog dialog) {
        for (Component c : dialog.getContentPane().getComponents()) {
            if (c instanceof JFileChooser chooser) return chooser;
            if (c instanceof Container container) {
                JFileChooser nested=fileChooser(container);
                if(nested!=null) return nested;
            }
        }
        return null;
    }
    private static JFileChooser fileChooser(Container parent) {
        for (Component c:parent.getComponents()) {
            if(c instanceof JFileChooser chooser)return chooser;
            if(c instanceof Container child) {
                JFileChooser nested=fileChooser(child);
                if(nested!=null) return nested;
            }
        }
        return null;
    }
    public static void main(String[] args) throws Exception {
        if(args.length!=2) throw new IllegalArgumentException("Usage: ChatNativeAuditRegression python3 output-path");
        if(GraphicsEnvironment.isHeadless()) {System.out.println("SKIP: actual visible Swing display unavailable (headless)");return;}
        Path target=Path.of(args[1]).toAbsolutePath().normalize();
        check(!Files.exists(target),"audit path already exists; CREATE_NEW only");
        AtomicReference<ShoppingDecisionDesktop> holder = new AtomicReference<>();
        try {
            ui(() -> {try {
                Constructor<ShoppingDecisionDesktop> c=ShoppingDecisionDesktop.class.getDeclaredConstructor(String.class);
                c.setAccessible(true);
                holder.set(c.newInstance(args[0]));
            }catch(Exception e){throw new RuntimeException(e);}});
        } catch(AWTError e) {
            if(e.getMessage()!=null && e.getMessage().contains("X11")) {
                System.out.println("SKIP: X11 display connection unavailable");return;
            }
            throw e;
        }
        ShoppingDecisionDesktop app=holder.get();
        JFrame frame=(JFrame)field(app,"frame");
        try {
            waitVersion(app,0);
            // 实际参考按钮点击只填写草稿，不改变版本。
            ui(() -> {
                JPanel refs=(JPanel)unsafeField(app,"chatReferences");
                click(refs,"打印机");
                check("打印机".equals(((JTextArea)unsafeField(app,"chatInput")).getText()),"draft not populated");
                check(((String)unsafeField(app,"chatState")).contains("\"version\": 0"),"draft auto-confirmed");
                ((JButton)unsafeField(app,"chatSend")).doClick();
            });
            waitVersion(app,1);
            ui(() -> {
                JTextArea input=(JTextArea)unsafeField(app,"chatInput");
                input.setText("【工程模拟，非亲戚本人逐项确认】河南家庭黑白打印，微信硬要求仅作严格测试假设");
                ((JButton)unsafeField(app,"chatSend")).doClick();
            });
            waitVersion(app,2);
            // 模拟明确字段批量修改，不将严格模拟误认为亲戚本人条件。
            ui(() -> {
                click((JPanel)unsafeField(app,"body"),"批量补充/修改");
                ((JTextArea)unsafeField(app,"chatInput")).setText(
                    "家中彩印是否必须：否\n" +
                    "能否外包彩印：是\n" +
                    "微信是否必须：必须\n" +
                    "是否接受首次App/扫码设置：接受\n" +
                    "微信打印方式：微信小程序直接打印\n" +
                    "打印机使用国家/地区：中国大陆河南省\n" +
                    "预算（元）：1000\n" +
                    "月打印页数：0-50");
                ((JButton)unsafeField(app,"chatSend")).doClick();
            });
            waitVersion(app,3);
            check(read(() -> ((String)field(app,"chatState")).contains("中国大陆河南省")),"deployment region not confirmed");
            // 单项改答：仅发送才使版本生效，旧结论要失效。
            ui(() -> {
                click((JPanel)unsafeField(app,"chatEdits"),"预算（元）");
                ((JTextArea)unsafeField(app,"chatInput")).setText("850");
                check(((String)unsafeField(app,"chatState")).contains("\"version\": 3"),"edit draft mutated answer");
                ((JButton)unsafeField(app,"chatSend")).doClick();
            });
            waitVersion(app,4);
            check(read(() -> ((String)field(app,"chatState")).contains("\"value\": 850")),"budget update not persisted");
            // 非法答案：真正触发桌面警示模态框；失败不落入已确认字段。
            ui(() -> {
                click((JPanel)unsafeField(app,"chatEdits"),"预算（元）");
                ((JTextArea)unsafeField(app,"chatInput")).setText("八百");
                ((JButton)unsafeField(app,"chatSend")).doClick();
            });
            until("invalid-answer error dialog", () -> visibleDialog("请检查")!=null);
            check(version(app)==4, "invalid answer changed state");
            ui(() -> {
                JDialog d=visibleDialog("请检查");
                check(d!=null,"error dialog disappeared");
                JOptionPane op=(JOptionPane)findComponent(d.getContentPane(),JOptionPane.class);
                check(op!=null,"error JOptionPane absent");
                op.setValue(JOptionPane.OK_OPTION);
            });
            until("error dialog closed", () -> visibleDialog("请检查")==null);
            check(read(() -> ((JLabel)field(app,"status")).getText().contains("本轮未确认")),
                    "UI did not report rejected answer");
            check(read(() -> ((JButton)field(app,"chatSend")).isEnabled()),"no recovery after bad input");
            // 新入口点击预览：实际用户确认模态框，再通过 JFileChooser 自主选择新路径保存。
            String preview = read(() -> (String)field(app,"chatReport"));
            check(preview.contains("中国大陆河南省") && preview.contains("\"transactions_enabled\": false"),
                    "report missing region/closed transactions");
            SwingUtilities.invokeLater(() -> click((JPanel)unsafeField(app,"body"),"预览/另存审计"));
            until("preview dialog", () -> visibleDialog("预览并编辑评审记录")!=null);
            ui(() -> {
                JDialog d=visibleDialog("预览并编辑评审记录");
                JOptionPane op=(JOptionPane)findComponent(d.getContentPane(),JOptionPane.class);
                check(op!=null,"preview dialog option pane absent");
                op.setValue(JOptionPane.OK_OPTION);
            });
            until("save dialog", () -> {
                for(Window w:Window.getWindows())
                    if(w instanceof JDialog d && d.isVisible() && fileChooser(d.getContentPane())!=null) return true;
                return false;
            });
            ui(() -> {
                JFileChooser chooser=null;
                for(Window w:Window.getWindows()) if(w instanceof JDialog d && d.isVisible()) {
                    chooser=fileChooser(d.getContentPane());
                    if(chooser!=null) break;
                }
                check(chooser!=null,"native JFileChooser missing");
                chooser.setSelectedFile(target.toFile());
                chooser.approveSelection();
            });
            until("created audit",() -> Files.exists(target));
            String exact=Files.readString(target,StandardCharsets.UTF_8);
            check(exact.equals(preview+"\n\n人工评审意见（请自行填写）：\n"),"UTF-8 readback does not match preview");
            check(exact.contains("\"purchase_recommendation_approved\": false")
                    && exact.contains("\"transactions_enabled\": false"),"purchase/transaction guard absent");
            System.out.println("PASS visible native Swing: draft/send/batch/edit/error-dialog recovery/manual preview + JFileChooser CREATE_NEW UTF-8 readback");
            System.out.println("AUDIT_FILE "+target);
            System.out.println("AUDIT_BYTES "+Files.size(target));
            // 保存后做跨品类切换、旧表单回退；不污染已保存的打印机审计快照。
            answer(app,"商品品类","手机");
            waitVersion(app,5);
            check(read(() -> ((JTextArea)field(app,"chatOutcome")).getText().contains("不会返回打印机候选")
                            || ((JTextArea)field(app,"chatOutcome")).getText().contains("尚无可用的专业商品材料")),
                    "phone case reused printer evidence");
            ui(() -> click((JPanel)unsafeField(app,"body"),"旧表单回退（实验）"));
            check(read(() -> ((JPanel)field(app,"body")).getComponent(1).isVisible()),"legacy one page not shown");
            ui(() -> click((JPanel)unsafeField(app,"body"),"返回对话主入口"));
            check(read(() -> ((JPanel)field(app,"body")).getComponent(0).isVisible()),"chat page not restored");
            System.out.println("PASS cross-category isolation and legacy form fallback/return");
        } finally {
            ui(frame::dispose);
        }
    }
    private static Object unsafeField(Object app,String name) {
        try {return field(app,name);}catch(Exception e){throw new RuntimeException(e);}
    }
    private static Component findComponent(Container parent,Class<?> cls) {
        for(Component c:parent.getComponents()) {
            if(cls.isInstance(c))return c;
            if(c instanceof Container child) {
                Component x=findComponent(child,cls);if(x!=null)return x;
            }
        }
        return null;
    }
}
