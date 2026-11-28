import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.Map;
public final class CognitionGuideRegression {
    static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
    public static void main(String[] args)throws Exception {
        String py=args[0];Path out=Path.of(args[1]);
        String s=DecisionWorksheetRegression.old(py,"","","").get("state_json");
        s=DecisionWorksheetRegression.old(py,s,"category","打印机").get("state_json");
        Map<String,String> normal=DecisionWorksheetRegression.old(py,s,"usage","家里想买打印机，不懂参数");
        s=normal.get("state_json");
        Map<String,String> via=DecisionWorksheetRegression.call(py,s,"null","guide","{}");
        for(String k:new String[]{"state_json","cognition_guide_json","cognition_context_json","guide_text","decision_note_json"})
            check(normal.get(k).equals(via.get(k)),"projection mismatch "+k);
        check(DecisionWorksheetRegression.call(py,s,"null","guide","{\"review_status\":\"approved\"}").containsKey("error"),"self approval admitted");
        Files.writeString(out.resolve("guide-bridge-context.json"),via.get("cognition_context_json"),StandardCharsets.UTF_8);
        Files.writeString(out.resolve("guide-bridge-note.json"),via.get("decision_note_json"),StandardCharsets.UTF_8);
        System.out.println("PASS actual Java guide stdin and legacy three-argument projection parity; malicious payload rejected");
    }
}
