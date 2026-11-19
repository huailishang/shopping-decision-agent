import java.nio.charset.StandardCharsets;
import java.util.*;

/** Java 到 Python 对话桥接的真实子进程回归，不涉及购物账户。 */
public final class ChatBridgeRegression {
    private static void check(boolean ok, String why) { if (!ok) throw new AssertionError(why); }
    private static Map<String,String> call(String py, String state, String field, String answer) throws Exception {
        List<String> argv = new ArrayList<>(List.of(py,"-m","shopping_decision.chat_bridge"));
        for (String s : new String[]{state,field,answer})
            argv.add(Base64.getEncoder().encodeToString(s.getBytes(StandardCharsets.UTF_8)));
        return DesktopBridgeClient.invoke(new ProcessBuilder(argv), 20_000);
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 1) throw new IllegalArgumentException("Usage: ChatBridgeRegression python3");
        String py = args[0];
        Map<String,String> initial = call(py,"","","");
        check("0".equals(initial.get("session_version")), "default version");
        check(initial.get("choices").contains("打印机"), "no references");
        check(!initial.get("state_json").contains("user_explicit"), "default confirmed");
        System.out.println("PASS references are drafts");

        Map<String,String> printer = call(py,initial.get("state_json"),"category","我想买打印机");
        check("1".equals(printer.get("session_version")), "send not confirmed");
        check("usage".equals(printer.get("prompt_field")), "wrong next question");
        System.out.println("PASS explicit category and next turn");

        Map<String,String> usage = call(py,printer.get("state_json"),"usage","家用打印，希望微信打印");
        Map<String,String> unknown = call(py,usage.get("state_json"),"needs_color","暂不确定");
        check(unknown.get("state_json").contains("deferred_fields"), "missing deferred");
        System.out.println("PASS unknown remains unknown");

        Map<String,String> updated = call(py,unknown.get("state_json"),"needs_color","否");
        check("4".equals(updated.get("session_version")), "edit version");
        check(updated.get("report_json").contains("\"transactions_enabled\": false"), "transaction boundary");
        System.out.println("PASS edit version and transaction block");

        Map<String,String> phone = call(py,updated.get("state_json"),"category","手机");
        check("unsupported".equals(phone.get("status")), "unscoped product not blocked");
        check(!phone.get("report_json").contains("HL-L1238W"), "printer facts leaked");
        System.out.println("PASS cross-category protection");

        Map<String,String> denied = call(py,phone.get("state_json"),"transactions_enabled","是");
        check(denied.containsKey("error"), "forbidden field");
        System.out.println("PASS illegal field rejected");
        System.out.println("ChatBridge Java subprocess regression: 6/6 PASS");
    }
}
