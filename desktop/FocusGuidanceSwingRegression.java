import javax.swing.*;
import java.awt.*;
import java.lang.reflect.Constructor;
import java.nio.file.*;
import java.util.concurrent.atomic.AtomicReference;

public final class FocusGuidanceSwingRegression {
    static void check(boolean b,String msg){DecisionWorksheetSwingRegression.check(b,msg);}
    static void ui(Runnable r)throws Exception{DecisionWorksheetSwingRegression.ui(r);}
    static Object field(Object a,String n){return DecisionWorksheetSwingRegression.field(a,n);}
    static String value(Object a,String n)throws Exception{return DecisionWorksheetSwingRegression.value(a,n);}
    static void await(Object a,String n,String s)throws Exception{DecisionWorksheetSwingRegression.await(a,n,s);}
    static void send(Object a,String s)throws Exception{DecisionWorksheetSwingRegression.send(a,s);}
    static void named(Object a,String n)throws Exception{DecisionWorksheetSwingRegression.named(a,n);}
    static void click(Object a,String n)throws Exception{DecisionWorksheetSwingRegression.click(a,n);}
    static String area(Object a,String n)throws Exception{
        AtomicReference<String> r=new AtomicReference<>();ui(()->r.set(((JTextArea)field(a,n)).getText()));return r.get();
    }
    static void log(Path p,Object a,String event)throws Exception{
        DecisionWorksheetSwingRegression.log(p,event+"\nFIELD="+value(a,"chatPromptField")+"\nSTATE="+value(a,"chatState")+"\nREPORT="+value(a,"chatReport")+"\nTRANSCRIPT="+area(a,"chatTranscript")+"\nNOTE="+value(a,"decisionNote"));
    }
    static void question(Object a,String f)throws Exception{
        for(int i=0;i<250;i++){if(value(a,"chatPromptField").equals(f))return;Thread.sleep(100);}
        throw new AssertionError("expected exact field "+f+" got "+value(a,"chatPromptField"));
    }
    static void reset(Object a,String usage)throws Exception{
        named(a,"新建空白会话");await(a,"chatState","\"version\": 0");
        question(a,"category");send(a,"打印机");question(a,"usage");send(a,usage);
        await(a,"chatState",usage);
    }
    static void pass(String id){System.out.println("PASS "+id+" native event chain");}
    public static void main(String[] args)throws Exception{
        check(!GraphicsEnvironment.isHeadless(),"native display required");
        Path out=Path.of(args[1]);Files.createDirectories(out);
        AtomicReference<Object> owner=new AtomicReference<>();
        ui(()->{try{Constructor<ShoppingDecisionDesktop> c=ShoppingDecisionDesktop.class.getDeclaredConstructor(String.class);c.setAccessible(true);owner.set(c.newInstance(args[0]));}catch(Exception e){throw new RuntimeException(e);}});
        Object a=owner.get();
        try{
            await(a,"chatState","\"version\": 0");
            reset(a,"扫描纸质资料存档");question(a,"requires_scan");
            check(area(a,"chatTranscript").contains("为什么问："),"focus explanation missing");
            check(value(a,"chatReport").contains("guide-functions"),"no admitted function explanation");
            log(out.resolve("F01-before.txt"),a,"rough scan request");
            send(a,"是");await(a,"chatState","\"requires_scan\": {");question(a,"needs_color");
            log(out.resolve("F01-confirmed.txt"),a,"explicit scan confirmation");
            send(a,"否");question(a,"device_deployment_region");
            send(a,"河南");question(a,"monthly_pages_range");
            send(a,"0-50");await(a,"chatState","\"monthly_pages_range\": {");
            check(value(a,"chatReport").contains("hp-scan")&&area(a,"chatTranscript").contains("核Brother HL-L1238W的扫描"),"concrete scan research absent");
            log(out.resolve("F01-after.txt"),a,"scan claim and concrete next research");pass("F01");
            reset(a,"想在家打印彩色照片");question(a,"needs_color");
            log(out.resolve("F02-before.txt"),a,"color question");
            send(a,"是");await(a,"chatState","\"needs_color\": {");question(a,"");
            check(area(a,"chatOutcome").contains("黑白"),"mono exclusion not visible");
            log(out.resolve("F02-after.txt"),a,"confirmed color; mono not fit");pass("F02");
            reset(a,"黑白作业偶尔彩印可外包");question(a,"needs_color");
            send(a,"否");question(a,"accepts_outsourced_color");
            log(out.resolve("F03-before.txt"),a,"outsourcing question");
            send(a,"是");await(a,"chatState","\"accepts_outsourced_color\": {");
            check(area(a,"chatGuide").contains("外部打印或暂缓购买：可考虑")&&area(a,"chatGuide").contains("未核当地费用与可达性"),"outsourcing scope or unknown fee missing");
            log(out.resolve("F03-after.txt"),a,"outsourcing allowed");pass("F03");
            reset(a,"需要机器自动双面");question(a,"requires_auto_duplex");
            log(out.resolve("F04-before.txt"),a,"duplex question");
            send(a,"是");await(a,"chatState","\"requires_auto_duplex\": {");question(a,"needs_color");
            DecisionWorksheetSwingRegression.batch(a,"needs_color:否\nrequires_scan:是\ndevice_deployment_region:河南\nmonthly_pages_range:0-50");
            await(a,"chatState","\"requires_scan\": {");
            String scanDuplex=value(a,"chatReport");
            check(scanDuplex.contains("hp-scan")&&scanDuplex.contains("hp-auto-duplex"),"separate model facts missing");
            check(!value(a,"chatPromptField").equals("requires_scan")&&!value(a,"chatPromptField").equals("requires_auto_duplex"),"confirmed hard condition repeated");
            log(out.resolve("F04-after.txt"),a,"both hard conditions confirmed; separate candidate evidence");pass("F04");
            reset(a,"常连续多周不用");question(a,"idle_weeks_pattern");
            log(out.resolve("F05-before.txt"),a,"idle question");
            send(a,"经常连续多周不用");await(a,"chatState","often_long");
            check(area(a,"chatOutcome").contains("恢复步骤"),"research not changed");
            named(a,"连续多周闲置情况");send(a,"暂不确定");await(a,"chatReport","\"answer_state\": \"deferred\"");
            named(a,"连续多周闲置情况");send(a,"通常每周都会用");await(a,"chatState","usually_short");
            named(a,"连续多周闲置情况");send(a,"撤回");await(a,"chatReport","\"answer_state\": \"withdrawn\"");
            log(out.resolve("F05-after.txt"),a,"idle confirmed, deferred, reconfirmed and withdrawn");pass("F05");
            reset(a,"扫描存档");question(a,"requires_scan");
            String before=value(a,"chatState");log(out.resolve("F06-before.txt"),a,"before draft");
            // Real reference button populates draft, not state.
            ui(()->{JButton b=DecisionWorksheetSwingRegression.find((JPanel)field(a,"chatReferences"),JButton.class,x->"是".equals(x.getText()));check(b!=null,"reference missing");b.doClick();});
            check(before.equals(value(a,"chatState")),"reference mutated state");
            ui(()->((JTextArea)field(a,"chatInput")).setText(""));
            check(before.equals(value(a,"chatState")),"draft cancel mutated state");
            send(a,"是");await(a,"chatState","\"requires_scan\": {");
            log(out.resolve("F06-after.txt"),a,"reference draft cancel and actual send");pass("F06");
            reset(a,"扫描存档");question(a,"requires_scan");
            Path reg=Path.of("knowledge","printer_cognition_guide_v1.json");byte[] original=Files.readAllBytes(reg);
            String txt=new String(original,java.nio.charset.StandardCharsets.UTF_8), key="\"hp-cn-home\": {\"revision\": 1, \"status\": \"active\"}";
            check(txt.contains(key),"registry fixture mismatch");
            DecisionWorksheetSwingRegression.batch(a,"budget_max_cny:1000");await(a,"chatState","\"budget_max_cny\": {");question(a,"requires_scan");
            before=value(a,"chatState");log(out.resolve("F07-before.txt"),a,"active source");
            try{
                Files.writeString(reg,txt.replace(key,key.replace("active","withdrawn")));
                click(a,"guideRefresh");
                CognitionGuideSwingRegression.waitGuide(a,"认知来源 hp-cn-home 已撤回、待核或不可用");
                check(before.equals(value(a,"chatState")),"withdrawal changed answers");
                check(area(a,"chatGuide").contains("部分激光打印机鼓粉分离"),"independent claim lost");
                log(out.resolve("F07-withdrawn.txt"),a,"withdrawn source; independent claim retained");
                Files.writeString(reg,txt.replace(key,key.replace("revision\": 1","revision\": 2")));
                click(a,"guideRefresh");
                await(a,"chatReport","\"revision\": 2");
                check(before.equals(value(a,"chatState")),"source changed answers");
                check(area(a,"chatTranscript").contains("当前专业依据待核"),"pending explanation absent");
                log(out.resolve("F07-after.txt"),a,"same-id newer revision not reviewed");pass("F07");
            }finally{Files.write(reg,original);}
            reset(a,"家庭打印");question(a,"needs_color");
            send(a,"否");await(a,"chatState","\"needs_color\": {");
            DecisionWorksheetSwingRegression.batch(a,"device_deployment_region:河南\nmonthly_pages_range:0-50\nidle_weeks_pattern:暂不确定");
            await(a,"chatReport","\"answer_state\": \"deferred\"");
            click(a,"worksheetCreate");await(a,"worksheetJson","guide_reference");
            ui(()->{DecisionWorksheetSwingRegression.edit(a,"","pages","0");DecisionWorksheetSwingRegression.edit(a,"","months","");});
            click(a,"worksheetApply");await(a,"worksheetJson","\"pages\": 0");
            Path saved=out.resolve("F08-saved.json");
            log(out.resolve("F08-before.txt"),a,"before save");
            SwingUtilities.invokeLater(()->((JButton)field(a,"worksheetSave")).doClick());
            DecisionWorksheetSwingRegression.chooser(saved,false);
            for(int i=0;i<100&&!Files.isRegularFile(saved);i++)Thread.sleep(100);
            check(Files.isRegularFile(saved),"saved worksheet absent");
            String bytes=Files.readString(saved);check(!bytes.contains("guidance_focus"),"cached focus saved");
            named(a,"新建空白会话");await(a,"chatState","\"version\": 0");
            SwingUtilities.invokeLater(()->((JButton)field(a,"worksheetRestore")).doClick());
            DecisionWorksheetSwingRegression.chooser(saved,false);DecisionWorksheetSwingRegression.confirm();
            await(a,"chatState","\"needs_color\": {");
            check(value(a,"chatReport").contains("guidance_focus"),"restore no current focus");
            check(bytes.equals(Files.readString(saved)),"saved bytes altered");
            String restored=value(a,"worksheetJson");
            check(restored.contains("\"pages\": 0")&&restored.contains("\"months\": null"),"zero/unknown lost");
            check(value(a,"chatReport").contains("\"answer_state\": \"deferred\""),"deferred lost");
            log(out.resolve("F08-restored.txt"),a,"fresh Python restore with zero/unknown/deferred");
            DecisionWorksheetSwingRegression.batch(a,"device_deployment_region:日本");await(a,"chatState","日本");
            check(!value(a,"chatState").equals(before),"region not changed");
            ui(()->check(((java.util.Map<?,?>)field(a,"worksheetInputs")).isEmpty(),"stale costs still editable"));
            String regionState=value(a,"chatState");
            Path poisoned=out.resolve("F08-cached-winner.json");
            Files.writeString(poisoned,"{\"winner\":\"HP M232dw\","+bytes.substring(1));
            SwingUtilities.invokeLater(()->((JButton)field(a,"worksheetRestore")).doClick());
            DecisionWorksheetSwingRegression.chooser(poisoned,false);DecisionWorksheetSwingRegression.dismissWarning();
            check(regionState.equals(value(a,"chatState")),"cached winner changed state");
            log(out.resolve("F08-after.txt"),a,"region changed; stale costs removed; cached winner rejected");pass("F08");
            reset(a,"家庭打印");question(a,"needs_color");
            log(out.resolve("F11-before.txt"),a,"before batch");
            DecisionWorksheetSwingRegression.batch(a,"needs_color:否\nrequires_scan:否\nrequires_auto_duplex:否");
            await(a,"chatState","\"requires_auto_duplex\": {");
            check(!value(a,"chatPromptField").equals("requires_scan")&&!value(a,"chatPromptField").equals("requires_auto_duplex"),"expert answer repeated");
            log(out.resolve("F11-after.txt"),a,"expert batch preserved");pass("F11");
            Path note=out.resolve("F12-note.json");before=value(a,"chatState");
            String noteText=value(a,"decisionNote");
            check(noteText.contains("\"guidance_focus\""),"note focus missing");
            log(out.resolve("F12-before.txt"),a,"before note preview");
            SwingUtilities.invokeLater(()->((JButton)field(a,"notePreview")).doClick());
            CognitionGuideSwingRegression.previewNote(true);DecisionWorksheetSwingRegression.chooser(note,false);
            for(int i=0;i<100&&!Files.isRegularFile(note);i++)Thread.sleep(100);
            check(Files.isRegularFile(note)&&Files.readString(note).equals(noteText),"note save mismatch");
            SwingUtilities.invokeLater(()->((JButton)field(a,"notePreview")).doClick());
            CognitionGuideSwingRegression.previewNote(false);
            check(before.equals(value(a,"chatState"))&&Files.readString(note).equals(noteText),"cancel changed state/file");
            SwingUtilities.invokeLater(()->((JButton)field(a,"notePreview")).doClick());
            CognitionGuideSwingRegression.previewNote(true);DecisionWorksheetSwingRegression.chooser(note,false);DecisionWorksheetSwingRegression.dismissWarning();
            check(before.equals(value(a,"chatState"))&&Files.readString(note).equals(noteText),"failed overwrite changed state/file");
            log(out.resolve("F12-after.txt"),a,"note saved, preview cancelled, overwrite refused");pass("F12");
            System.out.println("FOCUS_GUIDANCE_NATIVE_PASS");
        }finally{ui(()->((JFrame)field(a,"frame")).dispose());}
    }
}
