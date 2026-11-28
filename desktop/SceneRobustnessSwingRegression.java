import javax.swing.*;
import java.awt.*;
import java.lang.reflect.Constructor;
import java.nio.file.*;
import java.util.concurrent.atomic.AtomicReference;
public final class SceneRobustnessSwingRegression {
    static Object open(String py)throws Exception{
        AtomicReference<Object> owner=new AtomicReference<>();
        FocusGuidanceSwingRegression.ui(()->{try{Constructor<ShoppingDecisionDesktop> c=ShoppingDecisionDesktop.class.getDeclaredConstructor(String.class);c.setAccessible(true);owner.set(c.newInstance(py));}catch(Exception e){throw new RuntimeException(e);}});
        Object a=owner.get(); FocusGuidanceSwingRegression.await(a,"chatState","\"version\": 0");return a;
    }
    static void close(Object a)throws Exception{FocusGuidanceSwingRegression.ui(()->((JFrame)FocusGuidanceSwingRegression.field(a,"frame")).dispose());}
    static void answer(Object a,String field,String answer)throws Exception{FocusGuidanceSwingRegression.question(a,field);FocusGuidanceSwingRegression.send(a,answer);FocusGuidanceSwingRegression.await(a,"chatState","\""+field+"\": {");}
    static void feature(Object a,Path out,String id,String usage,String field,String fact,String query)throws Exception{
        FocusGuidanceSwingRegression.reset(a,usage);FocusGuidanceSwingRegression.question(a,field);
        FocusGuidanceSwingRegression.log(out.resolve(id+"-before.txt"),a,"ordinary usage, no auto answer");
        FocusGuidanceSwingRegression.check(!FocusGuidanceSwingRegression.value(a,"chatState").contains("\""+field+"\": {"),"auto answer");
        answer(a,field,"是");answer(a,"needs_color","否");answer(a,"device_deployment_region","河南");answer(a,"monthly_pages_range","0-50");
        FocusGuidanceSwingRegression.check(FocusGuidanceSwingRegression.value(a,"chatReport").contains(fact),"candidate fact missing");
        FocusGuidanceSwingRegression.check(FocusGuidanceSwingRegression.area(a,"chatTranscript").contains(query),"candidate research missing");
        FocusGuidanceSwingRegression.log(out.resolve(id+"-after.txt"),a,"explicit answer to candidate research");
    }
    public static void main(String[] args)throws Exception{
        FocusGuidanceSwingRegression.check(!GraphicsEnvironment.isHeadless(),"native display required");Path out=Path.of(args[1]);Object a=open(args[0]);Path saved=out.resolve("scene-withdrawn-saved.json");
        try{
            feature(a,out,"S01","把纸本收据做成电子版","requires_scan","hp-scan","核Brother HL-L1238W的扫描");
            feature(a,out,"S02","无需扫描，主要想让机器自动翻纸","requires_auto_duplex","hp-auto-duplex","核Brother HL-L1238W的自动双面");
            FocusGuidanceSwingRegression.reset(a,"旅行三个月，回来再打印");FocusGuidanceSwingRegression.question(a,"idle_weeks_pattern");
            FocusGuidanceSwingRegression.log(out.resolve("S03-before.txt"),a,"interval clarification");
            answer(a,"idle_weeks_pattern","经常连续多周不用");FocusGuidanceSwingRegression.await(a,"chatState","often_long");
            FocusGuidanceSwingRegression.check(FocusGuidanceSwingRegression.area(a,"chatOutcome").contains("恢复步骤"),"idle research missing");
            FocusGuidanceSwingRegression.log(out.resolve("S03-after.txt"),a,"interval research");
            FocusGuidanceSwingRegression.named(a,"连续多周闲置情况");FocusGuidanceSwingRegression.send(a,"撤回");FocusGuidanceSwingRegression.await(a,"chatReport","\"answer_state\": \"withdrawn\"");
            FocusGuidanceSwingRegression.click(a,"worksheetCreate");FocusGuidanceSwingRegression.await(a,"worksheetJson","guide_reference");
            Object owner=a;SwingUtilities.invokeLater(()->((JButton)FocusGuidanceSwingRegression.field(owner,"worksheetSave")).doClick());DecisionWorksheetSwingRegression.chooser(saved,false);
            for(int i=0;i<100&&!Files.isRegularFile(saved);i++)Thread.sleep(100);
            FocusGuidanceSwingRegression.check(Files.isRegularFile(saved),"save failed");FocusGuidanceSwingRegression.log(out.resolve("S04-withdrawn.txt"),a,"withdrawn and saved");
        }finally{close(a);}
        a=open(args[0]);try{
            Object owner=a;SwingUtilities.invokeLater(()->((JButton)FocusGuidanceSwingRegression.field(owner,"worksheetRestore")).doClick());DecisionWorksheetSwingRegression.chooser(saved,false);DecisionWorksheetSwingRegression.confirm();
            FocusGuidanceSwingRegression.await(a,"chatReport","\"answer_state\": \"withdrawn\"");
            FocusGuidanceSwingRegression.check(!FocusGuidanceSwingRegression.value(a,"chatState").contains("often_long"),"withdrawn preference revived");
            FocusGuidanceSwingRegression.check(FocusGuidanceSwingRegression.value(a,"chatReport").contains("\"transactions_enabled\": false"),"transaction revived");
            FocusGuidanceSwingRegression.log(out.resolve("S04-restored.txt"),a,"new window restored withdrawal without revival");
            System.out.println("SCENE_ROBUSTNESS_NATIVE_PASS");
        }finally{close(a);}
    }
}
