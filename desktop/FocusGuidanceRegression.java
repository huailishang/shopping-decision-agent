import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.Map;
public final class FocusGuidanceRegression {
    static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
    public static void main(String[] args)throws Exception {
        String py=args[0];Path out=Path.of(args[1]);
        String s=DecisionWorksheetRegression.old(py,"","","").get("state_json");
        s=DecisionWorksheetRegression.old(py,s,"category","打印机").get("state_json");
        Map<String,String> normal=DecisionWorksheetRegression.old(py,s,"usage","扫描纸质资料存档");
        s=normal.get("state_json");
        Map<String,String> via=DecisionWorksheetRegression.call(py,s,"null","guide","{}");
        for(String k:new String[]{"state_json","guidance_focus_json","guidance_focus_text","cognition_context_json","decision_note_json","prompt_field","prompt"})
            check(normal.get(k).equals(via.get(k)),"projection mismatch "+k);
        check("requires_scan".equals(via.get("prompt_field")),"not scan");
        check(via.get("guidance_focus_json").contains("guide-functions"),"missing evidence");
        check(DecisionWorksheetRegression.call(py,s,"null","guide","{\"guidance_focus\":{\"field\":\"budget_scope\"}}").containsKey("error"),"injected focus accepted");
        Files.writeString(out.resolve("focus-bridge.json"),via.get("guidance_focus_json"),StandardCharsets.UTF_8);
        Files.writeString(out.resolve("focus-bridge-context.json"),via.get("cognition_context_json"),StandardCharsets.UTF_8);
        Files.writeString(out.resolve("focus-bridge-note.json"),via.get("decision_note_json"),StandardCharsets.UTF_8);
        System.out.println("PASS focus actual Java bridge parity and injection rejection");
    }
}
