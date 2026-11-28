import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
public final class DecisionWorksheetRegression {
    static void check(boolean ok,String why){if(!ok)throw new AssertionError(why);}
    static Map<String,String> old(String py,String s,String f,String a)throws Exception{
        List<String> cmd=new ArrayList<>(List.of(py,"-m","shopping_decision.chat_bridge"));
        for(String x:List.of(s,f,a))cmd.add(Base64.getEncoder().encodeToString(x.getBytes(StandardCharsets.UTF_8)));
        return DesktopBridgeClient.invoke(new ProcessBuilder(cmd),20000);
    }
    static Map<String,String> call(String py,String s,String w,String action,String payload)throws Exception{
        String req="{\"schema_version\":1,\"action\":\""+action+"\",\"state\":"+s+",\"worksheet\":"+w+",\"payload\":"+payload+"}";
        return DesktopBridgeClient.invoke(new ProcessBuilder(py,"-m","shopping_decision.chat_bridge","--worksheet-stdin"),20000,req.getBytes(StandardCharsets.UTF_8));
    }
    public static void main(String[] args)throws Exception{
        String py=args[0];Path out=Path.of(args[1]);String s=old(py,"","","").get("state_json");
        s=old(py,s,"category","打印机").get("state_json");
        var created=call(py,s,"null","create","{}");check(created.containsKey("worksheet_json"),"create failed");
        String w=created.get("worksheet_json");
        var zero=call(py,s,w,"edit","{\"candidate\":null,\"field\":\"pages\",\"value\":0}");
        check(zero.get("worksheet_json").contains("\"pages\": 0"),"zero lost");
        check(call(py,s,w,"edit","{\"candidate\":null,\"field\":\"months\",\"value\":0}").containsKey("error"),"invalid months accepted");
        check(call(py,s,w,"preview","{}").containsKey("worksheet_json"),"preview failed");
        Files.writeString(out.resolve("worksheet-bridge-zero.json"),zero.get("worksheet_json"),StandardCharsets.UTF_8);
        System.out.println("PASS Java actual worksheet stdin bridge create/zero/invalid/preview");
    }
}
