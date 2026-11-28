import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.Map;
public final class SceneRobustnessRegression {
    public static void main(String[] args)throws Exception {
        String py=args[0]; Path out=Path.of(args[1]);
        String[][] scenes={{"把纸本收据做成电子版","requires_scan"},{"无需扫描，主要想让机器自动翻纸","requires_auto_duplex"},{"旅行三个月，回来再打印","idle_weeks_pattern"}};
        for(int i=0;i<scenes.length;i++){
            String s=DecisionWorksheetRegression.old(py,"","","").get("state_json");
            s=DecisionWorksheetRegression.old(py,s,"category","打印机").get("state_json");
            Map<String,String> normal=DecisionWorksheetRegression.old(py,s,"usage",scenes[i][0]); s=normal.get("state_json");
            Map<String,String> via=DecisionWorksheetRegression.call(py,s,"null","guide","{}");
            FocusGuidanceRegression.check(scenes[i][1].equals(via.get("prompt_field")),"wrong field "+i);
            for(String k:new String[]{"state_json","prompt_field","prompt","guidance_focus_json","cognition_context_json","decision_note_json"})FocusGuidanceRegression.check(normal.get(k).equals(via.get(k)),"projection mismatch "+k);
            FocusGuidanceRegression.check(!s.contains("\""+scenes[i][1]+"\": {"),"automatic confirmation");
            Files.writeString(out.resolve("scene-bridge-"+i+".txt"),via.toString(),StandardCharsets.UTF_8);
        }
        System.out.println("PASS scene actual Java bridge parity");
    }
}
