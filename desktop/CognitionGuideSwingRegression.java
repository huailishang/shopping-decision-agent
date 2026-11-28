import javax.swing.*;
import java.awt.*;
import java.lang.reflect.Constructor;
import java.nio.file.*;
import java.util.concurrent.atomic.AtomicReference;

/** First native event slice. Final frozen acceptance marker intentionally withheld until all required chains run. */
public final class CognitionGuideSwingRegression {
    static void check(boolean b,String msg){DecisionWorksheetSwingRegression.check(b,msg);}
    static void ui(Runnable r)throws Exception{DecisionWorksheetSwingRegression.ui(r);}
    static Object field(Object o,String n){return DecisionWorksheetSwingRegression.field(o,n);}
    static String value(Object o,String n)throws Exception{return DecisionWorksheetSwingRegression.value(o,n);}
    static void await(Object o,String n,String s)throws Exception{DecisionWorksheetSwingRegression.await(o,n,s);}
    static void send(Object o,String s)throws Exception{DecisionWorksheetSwingRegression.send(o,s);}
    static void named(Object o,String s)throws Exception{DecisionWorksheetSwingRegression.named(o,s);}
    static String guide(Object o)throws Exception{
        AtomicReference<String> v=new AtomicReference<>();
        ui(()->v.set(((JTextArea)field(o,"chatGuide")).getText()));return v.get();
    }
    static void log(Path p,String s)throws Exception{DecisionWorksheetSwingRegression.log(p,s);}
    static void previewNote(boolean ok)throws Exception {
        for(int i=0;i<150;i++){
            AtomicReference<Boolean> done=new AtomicReference<>(false);
            ui(()->{for(Window w:Window.getWindows())if(w.isShowing()&&w instanceof JDialog d&&d.getTitle().contains("预览决定说明")){
                JOptionPane pane=DecisionWorksheetSwingRegression.find(w,JOptionPane.class,x->true);
                if(pane!=null){pane.setValue(ok?JOptionPane.OK_OPTION:JOptionPane.CANCEL_OPTION);done.set(true);return;}
            }});
            if(done.get())return;Thread.sleep(100);
        }
        throw new AssertionError("decision note preview absent");
    }
    static void waitGuide(Object a,String t)throws Exception{
        for(int i=0;i<250;i++){if(guide(a).contains(t))return;Thread.sleep(100);}
        throw new AssertionError("guide not updated "+t);
    }
    public static void main(String[] args)throws Exception{
        check(!GraphicsEnvironment.isHeadless(),"native display required");
        Path out=Path.of(args[1]); Files.createDirectories(out);
        AtomicReference<Object> owner=new AtomicReference<>();
        ui(()->{try{Constructor<ShoppingDecisionDesktop> c=ShoppingDecisionDesktop.class.getDeclaredConstructor(String.class);c.setAccessible(true);owner.set(c.newInstance(args[0]));}catch(Exception e){throw new RuntimeException(e);}});
        Object a=owner.get();
        try{
            await(a,"chatState","\"version\": 0");
            send(a,"打印机");await(a,"chatState","\"category\": {");
            send(a,"家里想买打印机，不懂参数");await(a,"chatState","不懂参数");
            String before=value(a,"chatState");
            ui(()->{
                JTabbedPane tabs=DecisionWorksheetSwingRegression.find((JFrame)field(a,"frame"),JTabbedPane.class,x->x.indexOfTab("选购前先看")>=0);
                check(tabs!=null,"guide tab missing");tabs.setSelectedIndex(tabs.indexOfTab("选购前先看"));
            });
            check(guide(a).contains("长期耗材成本"),"guide not displayed");
            check(guide(a).contains("来源："),"source not displayed");
            check(before.equals(value(a,"chatState")),"view confirmed demand");
            log(out.resolve("G01-guide.txt"),guide(a)+"\n"+value(a,"chatReport"));
            System.out.println("PASS G01 native coarse request and guide");
            check(guide(a).contains("发布：")&&guide(a).contains("获取：")&&guide(a).contains("定位："),"source detail absent");
            log(out.resolve("G03-source-details.txt"),guide(a));
            System.out.println("PASS G03 native source details and parameter explanation");
            named(a,"连续多周闲置情况");
            named(a,"经常连续多周不用");
            check(before.equals(value(a,"chatState")),"draft changed demand");
            log(out.resolve("G04-draft.txt"),before+"\n"+guide(a));
            System.out.println("PASS G04 native reference only drafts");
            DecisionWorksheetSwingRegression.click(a,"chatSend");
            await(a,"chatState","often_long");
            check(DecisionWorksheetSwingRegression.outcome(a).contains("连续多周不用后的恢复步骤"),"research not changed");
            log(out.resolve("G05-confirmed.txt"),DecisionWorksheetSwingRegression.outcome(a)+"\n"+value(a,"chatReport"));
            System.out.println("PASS G05 native explicit confirmation and changed research");
            named(a,"连续多周闲置情况");send(a,"暂不确定");await(a,"chatReport","\"answer_state\": \"deferred\"");
            named(a,"连续多周闲置情况");send(a,"通常每周都会用");await(a,"chatState","usually_short");
            named(a,"连续多周闲置情况");send(a,"撤回");await(a,"chatReport","\"answer_state\": \"withdrawn\"");
            log(out.resolve("G06-withdrawn.txt"),value(a,"chatReport"));
            System.out.println("PASS G06 native defer, confirm, withdraw");
            named(a,"家中彩印是否必须");send(a,"是");await(a,"chatState","\"needs_color\": {");
            check(guide(a).contains("黑白激光：不适用"),"color hard requirement not visible");
            check(guide(a).contains("喷墨或其他彩色路线：需要研究"),"alternative route missing");
            log(out.resolve("G02-color.txt"),guide(a)+"\n"+value(a,"chatReport"));
            named(a,"家中彩印是否必须");send(a,"否");await(a,"chatState","\"value\": false");
            named(a,"能否外包彩印");send(a,"是");await(a,"chatState","accepts_outsourced_color");
            check(guide(a).contains("外部打印或暂缓购买：可考虑"),"outsourcing route missing");
            log(out.resolve("G02-outsourced.txt"),guide(a)+"\n"+value(a,"chatReport"));
            System.out.println("PASS G02 native color and outsourcing route decisions");
            named(a,"连续多周闲置情况");send(a,"经常连续多周不用");await(a,"chatState","often_long");
            DecisionWorksheetSwingRegression.click(a,"worksheetCreate");await(a,"worksheetJson","guide_reference");
            Path saved=out.resolve("G14-saved.json");
            SwingUtilities.invokeLater(()->((JButton)field(a,"worksheetSave")).doClick());
            DecisionWorksheetSwingRegression.chooser(saved,false);
            for(int i=0;i<100&&!Files.isRegularFile(saved);i++)Thread.sleep(100);
            check(Files.isRegularFile(saved),"saved worksheet absent");
            String savedText=Files.readString(saved);
            check(savedText.contains("guide_reference")&&savedText.contains("often_long"),"saved inputs and guide references absent");
            check(!savedText.contains("guide_text")&&!savedText.contains("scenario_preference"),"cached results saved");
            named(a,"新建空白会话");await(a,"chatState","\"version\": 0");
            check(!guide(a).contains("连续多周不用后的恢复步骤"),"old guide leaked");
            SwingUtilities.invokeLater(()->((JButton)field(a,"worksheetRestore")).doClick());
            DecisionWorksheetSwingRegression.chooser(saved,false);
            DecisionWorksheetSwingRegression.confirm();
            await(a,"chatState","often_long");
            check(guide(a).contains("连续多周不用后的恢复步骤"),"restored guide did not recompute");
            check(value(a,"chatReport").contains("\"transactions_enabled\": false"),"restore enabled transactions");
            check(savedText.equals(Files.readString(saved)),"restore modified saved input");
            log(out.resolve("G14-restored.txt"),guide(a)+"\n"+value(a,"chatReport"));
            System.out.println("PASS G14 native save and new-process restore of guide inputs");
            // Controlled revision/withdrawal of the new local registry only; original bytes restored.
            Path registry=Path.of("knowledge","printer_cognition_guide_v1.json");
            byte[] original=Files.readAllBytes(registry);
            String originalText=new String(original,java.nio.charset.StandardCharsets.UTF_8);
            String key="\"rtings-cost-method-2021\": {\"revision\": 1, \"status\": \"active\"}";
            check(originalText.contains(key),"unexpected registry baseline");
            String unchanged=value(a,"chatState"),oldNote=value(a,"decisionNote");
            log(out.resolve("G13-before.txt"),oldNote);
            try {
                Files.writeString(registry,originalText.replace(key,key.replace("active","withdrawn")));
                DecisionWorksheetSwingRegression.click(a,"guideRefresh");
                waitGuide(a,"认知来源 rtings-cost-method-2021 已撤回");
                check(unchanged.equals(value(a,"chatState")),"withdrawal changed explicit answers");
                check(!guide(a).contains("单页耗材成本与长期总费用不同"),"withdrawn claim displayed");
                check(guide(a).contains("有的打印机兼有扫描和自动双面"),"independent claim lost");
                log(out.resolve("G13-withdrawn.txt"),guide(a)+"\n"+value(a,"chatReport"));
                Files.writeString(registry,originalText.replace(key,key.replace("revision\": 1","revision\": 2")));
                String prev=value(a,"decisionNote");
                DecisionWorksheetSwingRegression.click(a,"guideRefresh");
                for(int i=0;i<250&&prev.equals(value(a,"decisionNote"));i++)Thread.sleep(100);
                check(!prev.equals(value(a,"decisionNote")),"revision not recomputed");
                check(unchanged.equals(value(a,"chatState")),"new revision changed answers");
                check(!guide(a).contains("单页耗材成本与长期总费用不同"),"unreviewed revision approved");
                log(out.resolve("G13-revision2.txt"),guide(a)+"\n"+value(a,"chatReport"));
            } finally {Files.write(registry,original);}
            DecisionWorksheetSwingRegression.click(a,"guideRefresh");waitGuide(a,"单页耗材成本与长期总费用不同");
            check(unchanged.equals(value(a,"chatState")),"refresh changed answers");
            log(out.resolve("G13-recovered.txt"),guide(a)+"\n"+value(a,"chatReport"));
            System.out.println("PASS G13 native withdrawn and same-id unreviewed revision; current input preserved");
            // Actual preview, save, cancel and refused overwrite.
            Path note=out.resolve("G15-decision-note.json");
            String noteBefore=value(a,"decisionNote");
            SwingUtilities.invokeLater(()->((JButton)field(a,"notePreview")).doClick());
            previewNote(true);DecisionWorksheetSwingRegression.chooser(note,false);
            for(int i=0;i<100&&!Files.isRegularFile(note);i++)Thread.sleep(100);
            check(Files.isRegularFile(note),"decision note missing");
            String noteText=Files.readString(note);
            check(noteText.equals(noteBefore),"saved note differs from preview");
            check(noteText.contains("\"guide_version\"")&&noteText.contains("\"cognition_sources\"")&&noteText.contains("\"transactions_enabled\": false"),"note evidence or guard absent");
            System.out.println("PASS G15 native decision note preview and save");
            SwingUtilities.invokeLater(()->((JButton)field(a,"notePreview")).doClick());
            previewNote(false);
            check(noteText.equals(Files.readString(note)),"preview cancel modified file");
            Path cancelled=out.resolve("G16-cancelled.json");
            SwingUtilities.invokeLater(()->((JButton)field(a,"notePreview")).doClick());
            previewNote(true);DecisionWorksheetSwingRegression.chooser(cancelled,true);
            check(!Files.exists(cancelled),"cancel created file");
            SwingUtilities.invokeLater(()->((JButton)field(a,"notePreview")).doClick());
            previewNote(true);DecisionWorksheetSwingRegression.chooser(note,false);
            DecisionWorksheetSwingRegression.dismissWarning();
            check(noteText.equals(Files.readString(note)),"overwrite changed existing note");
            check(unchanged.equals(value(a,"chatState")),"cancel or failure changed state");
            log(out.resolve("G16-note-cancel.txt"),"preview cancelled; chooser cancelled; overwrite refused; previous bytes/state unchanged");
            System.out.println("PASS partial G16 note cancel and refused overwrite");
            // Invalid explicit draft must leave the already valid session intact.
            named(a,"连续多周闲置情况");
            SwingUtilities.invokeLater(()->{
                ((JTextArea)field(a,"chatInput")).setText("错误的枚举");
                ((JButton)field(a,"chatSend")).doClick();
            });
            DecisionWorksheetSwingRegression.dismissWarning();
            check(unchanged.equals(value(a,"chatState")),"bad input replaced state");
            // A real send followed immediately by a real new-session click in one EDT turn.
            // The prior worker's completion/cancellation event must not overwrite the new response.
            named(a,"主要用途");
            ui(()->{
                ((JTextArea)field(a,"chatInput")).setText("迟到旧会话标记");
                ((JButton)field(a,"chatSend")).doClick();
                JButton reset=DecisionWorksheetSwingRegression.find((JFrame)field(a,"frame"),JButton.class,x->"新建空白会话".equals(x.getText()));
                check(reset!=null,"new session missing");reset.doClick();
            });
            await(a,"chatState","\"version\": 0");
            Thread.sleep(1200);
            check(value(a,"chatState").contains("\"version\": 0")&&!value(a,"chatReport").contains("迟到旧会话标记"),"late reply overwrote fresh session");
            check(!guide(a).contains("连续多周不用后的恢复步骤"),"old guide leaked");
            log(out.resolve("G16-reset-and-fault.txt"),guide(a)+"\n"+value(a,"chatReport")+"\ninvalid enum refused; prior worker invalidated by actual new session event; note cancel/overwrite evidence separate");
            System.out.println("PASS G16 native invalid input, cancel, file safety and prior-worker reset");
            System.out.println("COGNITION_GUIDE_NATIVE_PASS");
        } finally{ui(()->((JFrame)field(a,"frame")).dispose());}
    }
}
