import javax.swing.*;
import java.awt.*;
import java.io.File;
import java.lang.reflect.Field;
import java.nio.file.*;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * 本轮程序化真实 Swing 窗口回归；不是人工真人试用。
 * Usage: CognitionSwingRegression <python-executable> <fresh-absolute-audit-path>
 * 保存路径仅 CREATE_NEW；不联网、不提交订单、不清理历史文件。
 */
public final class CognitionSwingRegression {
    private static void check(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
    }

    private static Object getField(Object obj, String name) throws Exception {
        Field field = obj.getClass().getDeclaredField(name);
        field.setAccessible(true);
        return field.get(obj);
    }

    private static void edt(Runnable action) throws Exception {
        SwingUtilities.invokeAndWait(action);
    }

    private static boolean condition(java.util.function.BooleanSupplier test) throws Exception {
        AtomicBoolean result = new AtomicBoolean();
        edt(() -> result.set(test.getAsBoolean()));
        return result.get();
    }

    private static void until(java.util.function.BooleanSupplier check, String reason) throws Exception {
        long deadline = System.nanoTime() + 15_000_000_000L;
        while (System.nanoTime() < deadline) {
            if (condition(check)) return;
            Thread.sleep(100);
        }
        throw new AssertionError("GUI wait expired: " + reason);
    }

    private static JFrame appFrame() {
        for (Window window : Window.getWindows()) {
            if (window instanceof JFrame frame && frame.isShowing()
                    && frame.getTitle().contains("购物智能体")) return frame;
        }
        return null;
    }

    private static <T extends Component> T find(Component top, Class<T> type,
                                                java.util.function.Predicate<T> predicate) {
        if (type.isInstance(top)) {
            T cast = type.cast(top);
            if (predicate.test(cast)) return cast;
        }
        if (top instanceof Container container) {
            for (Component child : container.getComponents()) {
                T item = find(child, type, predicate);
                if (item != null) return item;
            }
        }
        return null;
    }

    private static JButton button(JFrame frame, String label) {
        JButton item = find(frame, JButton.class, b -> label.equals(b.getText()));
        if (item == null) throw new AssertionError("missing JButton: " + label);
        return item;
    }

    private static void click(JFrame frame, String label) throws Exception {
        edt(() -> button(frame, label).doClick());
    }

    private static void change(Object controller, String field, String value) throws Exception {
        JTextField ref = (JTextField) getField(controller, field);
        edt(() -> ref.setText(value));
    }

    private static void changeArea(Object controller, String field, String value) throws Exception {
        JTextArea ref = (JTextArea) getField(controller, field);
        edt(() -> ref.setText(value));
    }

    private static void select(Object controller, String field, int index) throws Exception {
        JComboBox<?> ref = (JComboBox<?>) getField(controller, field);
        edt(() -> ref.setSelectedIndex(index));
    }

    private static String result(Object controller) throws Exception {
        JTextArea ref = (JTextArea) getField(controller, "result");
        return ref.getText();
    }

    private static void calculate(JFrame frame, Object controller) throws Exception {
        click(frame, "核对我的理解");
        click(frame, "确认并调用后端判断");
        until(() -> {
            try {return result(controller).contains("【本轮条件驱动的型号资格");}
            catch (Exception e) {return false;}
        }, "new criteria research result");
    }

    private static JDialog dialog(String titleText) {
        for (Window window : Window.getWindows()) {
            if (window instanceof JDialog d && d.isShowing()
                    && d.getTitle().contains(titleText)) return d;
        }
        return null;
    }

    public static void main(String[] args) throws Exception {
        if (args.length != 2) throw new IllegalArgumentException(
                "Usage: CognitionSwingRegression <python> <new-review-file>");
        Path audit = Path.of(args[1]).toAbsolutePath().normalize();
        if (Files.exists(audit) || !Files.isDirectory(audit.getParent()))
            throw new IllegalArgumentException("audit path must be new and parent directory must exist");
        ShoppingDecisionDesktop.main(new String[]{args[0]});
        until(() -> appFrame() != null, "real swing frame");
        JFrame frame = appFrame();
        Object controller = null;
        // Find controller via button's listener capturing ShoppingDecisionDesktop.
        JButton stepOne = button(frame, "下一步：补充条件");
        for (var listener : stepOne.getActionListeners()) {
            for (Field field : listener.getClass().getDeclaredFields()) {
                if (field.getType() == ShoppingDecisionDesktop.class) {
                    field.setAccessible(true);
                    controller = field.get(listener);
                    break;
                }
            }
        }
        check(controller != null, "unable to get displayed controller");
        Object app = controller;
        changeArea(app, "description", "预算千元内、月0–50页，家里黑白为主、偶尔去店里彩印，希望微信打印，可靠耐用");
        click(frame, "下一步：补充条件");
        change(app, "pages", "0–50");
        change(app, "budget", "1000");
        select(app, "color", 2);
        select(app, "outsourced", 1);
        calculate(frame, app);
        String original = result(app);
        check(original.contains("C-BUDGET 高于"), "original MSRP relation absent");
        check(original.contains("C-VOLUME 低于建议区间"), "original monthly volume relation absent");
        check(original.contains("购买资格：未核") || original.contains("不可购买"),
                "research-only safeguards missing");
        System.out.println("PASS GUI original model selection and source/unknown display");

        click(frame, "修改后重新判断");
        select(app, "scan", 1);
        calculate(frame, app);
        String scanning = result(app);
        check(scanning.contains("C-SCAN 未核"), "Brother scan unknown was lost");
        check(scanning.contains("C-SCAN 符合"), "HP scan evidence was lost");
        check(!scanning.equals(original), "old result unexpectedly persisted after edit");
        System.out.println("PASS GUI edit scan and recalculate");

        click(frame, "修改后重新判断");
        select(app, "color", 1);
        calculate(frame, app);
        String color = result(app);
        check(color.contains("HL-L1238W：本轮硬条件排除"), "Brother not excluded");
        check(color.contains("M232dw：本轮硬条件排除"), "HP not excluded");
        check(!color.contains("当前条件触发的取舍：必须扫描/复印或自动双面"),
                "excluded HP accidentally reintroduced via scan");
        System.out.println("PASS GUI color hard exclusion despite scan");

        click(frame, "修改后重新判断");
        select(app, "color", 2);
        change(app, "budget", "3000");
        calculate(frame, app);
        String rebudget = result(app);
        check(rebudget.contains("C-BUDGET 不高于"), "budget 3000 must update MSRP relation");
        check(rebudget.contains("当前预算3000元"), "old 1000 budget cached in current comparison");
        String report = (String) getField(app, "lastReport");
        check(report.contains("criteria_sha256"), "audit is missing criteria version");
        check(report.contains("hard_condition_override_blocked"), "audit missing condition precedence");
        check(report.contains("purchase_recommendation_approved"), "audit missing purchase safety flag");
        System.out.println("PASS GUI restore, rebudget, complete audit preview prepared");

        // 评估者G3：独立模拟用户明确表示必须微信小程序、设备在日本使用。
        click(frame, "修改后重新判断");
        select(app, "wechatRequired", 1);
        select(app, "wechatWorkflow", 1);
        change(app, "deviceDeploymentRegion", "日本");
        calculate(frame, app);
        String overseas = result(app);
        check(overseas.contains("部署地区范围：outside_mainland_china"),
                "deployment region not propagated to current research");
        check(overseas.contains("C-WECHAT 境外微信服务缺有效适用证据"),
                "overseas miniprogram must be pending, not match");
        check(!overseas.contains("C-WECHAT 符合"),
                "China-only source wrongly qualified an overseas device");
        check(overseas.contains("HL-L1238W：存在硬条件未知")
              && overseas.contains("M232dw：存在硬条件未知"),
                "both models must be pending for unsupported deployment region");
        System.out.println("PASS GUI overseas miniprogram hard evidence gate");

        // G1-R1：原文已经明确“必须微信打印”，用户选择转App但没有重复勾选。
        click(frame, "修改后重新判断");
        changeArea(app, "other", "必须微信打印");
        select(app, "wechatRequired", 0); // 未重复确认，不等于否定原话
        select(app, "wechatWorkflow", 2); // 文件转到厂商App
        change(app, "deviceDeploymentRegion", "");
        calculate(frame, app);
        String appTransfer = result(app);
        check(appTransfer.contains("wechat_transfer_to_app"),
                "normalized transfer-to-App requirement disappeared");
        check(appTransfer.contains("C-WECHAT App替代流程待实测"),
                "unconfirmed App transfer must execute C-WECHAT and stay pending");
        check(appTransfer.contains("HL-L1238W：存在硬条件未知")
              && appTransfer.contains("M232dw：存在硬条件未知"),
                "transfer-to-App hard requirement must not create eligible models");
        check(!appTransfer.contains("当前条件触发的取舍：只需黑白"),
                "pending App requirement improperly activated a model choice");
        System.out.println("PASS GUI raw transfer-to-App hard requirement without duplicate checkbox");

        // User-intentional preview and save, performed programmatically (not a human UX test).
        // 模态窗口启动需要放入事件队列；不能同步等待doClick返回。
        SwingUtilities.invokeLater(() -> button(frame, "预览本地评审记录").doClick());
        until(() -> dialog("预览并编辑评审记录") != null, "review modal");
        edt(() -> {
            JDialog d = dialog("预览并编辑评审记录");
            JOptionPane option = find(d, JOptionPane.class, o -> true);
            if (option == null) throw new AssertionError("missing review JOptionPane");
            option.setValue(JOptionPane.OK_OPTION);
        });
        until(() -> dialog("保存") != null || dialog("Save") != null, "save dialog");
        edt(() -> {
            JDialog d = dialog("保存") != null ? dialog("保存") : dialog("Save");
            JFileChooser chooser = find(d, JFileChooser.class, c -> true);
            if (chooser == null) throw new AssertionError("missing JFileChooser");
            chooser.setSelectedFile(audit.toFile());
            chooser.approveSelection();
        });
        long deadline = System.nanoTime() + 10_000_000_000L;
        while (!Files.exists(audit) && System.nanoTime() < deadline) Thread.sleep(100);
        check(Files.isRegularFile(audit), "audit not saved");
        String saved = Files.readString(audit);
        check(saved.contains("criteria_sha256") && saved.contains("C-BUDGET")
              && saved.contains("wechat_transfer_to_app")
              && saved.contains("other_workflow_unverified"),
                "saved audit missed the current App-transfer requirement");
        check(!saved.contains("已批准购买"), "unexpected purchase approval wording");
        System.out.println("PASS GUI explicit preview/save/readback; audit-bytes=" +
                           Files.size(audit) + "; path=" + audit);
        edt(frame::dispose);
        System.out.println("Cognition Swing actual-window programmatic regression: 7/7 PASS");
        System.exit(0);
    }
}
