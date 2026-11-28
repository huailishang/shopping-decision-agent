import javax.swing.*;
import java.awt.*;
import java.lang.reflect.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Predicate;
public final class DecisionWorksheetSwingRegression {
    static Object field(Object obj,String n){try{Field f=obj.getClass().getDeclaredField(n);f.setAccessible(true);return f.get(obj);}catch(Exception e){throw new RuntimeException(e);}}
    static void check(boolean b,String m){if(!b)throw new AssertionError(m);}
    static void ui(Runnable r)throws Exception{SwingUtilities.invokeAndWait(r);}
    static String value(Object a,String f)throws Exception{AtomicReference<String> r=new AtomicReference<>();ui(()->r.set((String)field(a,f)));return r.get();}
    static String outcome(Object a)throws Exception{AtomicReference<String> r=new AtomicReference<>();ui(()->r.set(((JTextArea)field(a,"chatOutcome")).getText()));return r.get();}
    static <T extends Component>T find(Component root,Class<T> c,Predicate<T> p){
        if(c.isInstance(root)&&p.test(c.cast(root)))return c.cast(root);
        if(root instanceof Container a)for(Component x:a.getComponents()){T y=find(x,c,p);if(y!=null)return y;}
        return null;
    }
    static void click(Object a,String n)throws Exception{ui(()->((JButton)field(a,n)).doClick());}
    static void named(Object a,String n)throws Exception{ui(()->{JButton b=find((JFrame)field(a,"frame"),JButton.class,x->n.equals(x.getText()));check(b!=null,"missing "+n);b.doClick();});}
    static void await(Object a,String n,String text)throws Exception{
        for(int i=0;i<250;i++){if(value(a,n).contains(text))return;Thread.sleep(100);}
        throw new AssertionError("timeout "+n+" expected "+text);
    }
    static void send(Object a,String text)throws Exception{ui(()->{((JTextArea)field(a,"chatInput")).setText(text);((JButton)field(a,"chatSend")).doClick();});}
    static void batch(Object a,String text)throws Exception{named(a,"批量补充/修改");send(a,text);}
    @SuppressWarnings("unchecked")
    static void edit(Object a,String cid,String key,String v){Map<String,JTextField> m=(Map<String,JTextField>)field(a,"worksheetInputs");JTextField t=m.get(cid+"\t"+key);check(t!=null,"missing field "+cid+key);t.setText(v);}
    static void chooser(Path path,boolean cancel)throws Exception{
        for(int i=0;i<100;i++){AtomicReference<Boolean> found=new AtomicReference<>(false);ui(()->{
            for(Window w:Window.getWindows())if(w.isShowing()&&w instanceof JDialog){
                JFileChooser c=find(w,JFileChooser.class,x->true);if(c!=null){found.set(true);if(cancel)c.cancelSelection();else{c.setSelectedFile(path.toFile());c.approveSelection();}return;}
            }});if(found.get())return;Thread.sleep(100);}
        throw new AssertionError("file chooser did not appear");
    }
    static void confirm()throws Exception{
        for(int i=0;i<150;i++){AtomicReference<Boolean> found=new AtomicReference<>(false);ui(()->{
            for(Window w:Window.getWindows())if(w.isShowing()&&w instanceof JDialog d&&d.getTitle().contains("核对保存条件")){
                JOptionPane p=find(w,JOptionPane.class,x->true);if(p!=null){found.set(true);p.setValue(JOptionPane.YES_OPTION);return;}
            }});if(found.get())return;Thread.sleep(100);}
        throw new AssertionError("restore confirmation did not appear");
    }
    static void dismissWarning()throws Exception{
        for(int i=0;i<150;i++){AtomicReference<Boolean> found=new AtomicReference<>(false);ui(()->{
            for(Window w:Window.getWindows())if(w.isShowing()&&w instanceof JDialog d&&d.getTitle().contains("请检查")){
                JOptionPane p=find(w,JOptionPane.class,x->true);if(p!=null){found.set(true);p.setValue(JOptionPane.OK_OPTION);return;}
            }});if(found.get())return;Thread.sleep(100);}
        throw new AssertionError("warning did not appear");
    }
    static void log(Path p,String s)throws Exception{Files.writeString(p,s,StandardCharsets.UTF_8);}
    public static void main(String[] args)throws Exception{
        check(!GraphicsEnvironment.isHeadless(),"native display required");
        Path out=Path.of(args[1]);AtomicReference<Object> owner=new AtomicReference<>();
        ui(()->{try{Constructor<ShoppingDecisionDesktop> c=ShoppingDecisionDesktop.class.getDeclaredConstructor(String.class);c.setAccessible(true);owner.set(c.newInstance(args[0]));}catch(Exception e){throw new RuntimeException(e);}});
        Object a=owner.get();
        try{
            await(a,"chatState","\"version\": 0");
            send(a,"打印机");await(a,"chatState","\"category\": {");
            batch(a,"usage:低频家庭打印\nneeds_color:否\naccepts_outsourced_color:是\nmonthly_pages_range:0-50\ndevice_deployment_region:中国大陆河南省\nwechat_required:否\nrequires_scan:否\nrequires_auto_duplex:否");
            await(a,"chatState","\"requires_auto_duplex\": {");
            click(a,"worksheetCreate");await(a,"worksheetJson","\"revision\": 0");
            ui(()->{
                edit(a,"","pages","1800");edit(a,"","months","36");
                for(String c:new String[]{"Brother HL-L1238W","HP M232dw"}){
                    edit(a,c,"hardware",c.startsWith("Brother")?"500":"550");edit(a,c,"starter","0");
                    edit(a,c,"toner_yield","1500");edit(a,c,"toner_price",c.startsWith("Brother")?"100":"50");
                    edit(a,c,"separate_drum","否");edit(a,c,"maintenance","0");
                }
            });
            click(a,"worksheetApply");await(a,"worksheetJson","\"revision\": 1");
            String before=outcome(a);check(before.contains("HP M232dw情景成本较低"),"initial preference: "+before);
            log(out.resolve("J02-before.txt"),before+"\n"+value(a,"chatReport"));
            ui(()->edit(a,"Brother HL-L1238W","starter","1500"));
            click(a,"worksheetCancel");
            check(value(a,"worksheetJson").contains("\"revision\": 1"),"cancel changed committed input");
            ui(()->edit(a,"Brother HL-L1238W","starter","1500"));click(a,"worksheetApply");await(a,"worksheetJson","\"revision\": 2");
            String after=outcome(a);check(after.contains("Brother HL-L1238W情景成本较低"),"flip failed: "+after);
            log(out.resolve("J02-after.txt"),after+"\n"+value(a,"chatReport"));
            System.out.println("PASS J02 native input and result cost flip; draft cancel");
            Path saved=out.resolve("J07-saved.json");
            SwingUtilities.invokeLater(()->((JButton)field(a,"worksheetSave")).doClick());chooser(saved,false);
            for(int i=0;i<100&&!Files.exists(saved);i++)Thread.sleep(100);
            check(Files.isRegularFile(saved),"save missing");
            String original=Files.readString(saved);
            named(a,"新建空白会话");await(a,"chatState","\"version\": 0");
            SwingUtilities.invokeLater(()->((JButton)field(a,"worksheetRestore")).doClick());chooser(saved,false);confirm();
            await(a,"worksheetJson","\"revision\": 2");
            String restored=outcome(a);check(restored.contains("Brother HL-L1238W情景成本较低"),"restore result");
            check(value(a,"chatReport").contains("\"transactions_enabled\": false"),"transaction guard");
            check(original.equals(Files.readString(saved)),"saved file changed");
            log(out.resolve("J07-restored.txt"),restored+"\n"+value(a,"chatReport"));
            System.out.println("PASS J07 native save and fresh session / Python process restore");
            Path cancelled=out.resolve("cancelled.json");
            SwingUtilities.invokeLater(()->((JButton)field(a,"worksheetSave")).doClick());chooser(cancelled,true);
            check(!Files.exists(cancelled),"cancel created file");
            System.out.println("PASS save dialog cancel");
            // Existing-file save must fail without touching the committed worksheet or old bytes.
            String committed=value(a,"worksheetJson");
            SwingUtilities.invokeLater(()->((JButton)field(a,"worksheetSave")).doClick());chooser(saved,false);dismissWarning();
            check(original.equals(Files.readString(saved)),"existing file corrupted");
            check(committed.equals(value(a,"worksheetJson")),"save failure changed current worksheet");
            log(out.resolve("J09-after.txt"),"existing file intact; cancel left no file; committed input unchanged\n"+committed);
            System.out.println("PASS J09 native draft cancel, file cancel and refused overwrite");
            // Explicit zero is not blank; restoring the shared basis must recover comparison.
            log(out.resolve("J04-before.txt"),outcome(a)+"\n"+committed);
            ui(()->edit(a,"","pages","0"));click(a,"worksheetApply");await(a,"worksheetJson","\"revision\": 3");
            check(value(a,"worksheetJson").contains("\"pages\": 0"),"zero lost");
            ui(()->edit(a,"","pages",""));click(a,"worksheetApply");await(a,"worksheetJson","\"revision\": 4");
            check(value(a,"worksheetJson").contains("\"pages\": null"),"blank not unknown");
            check(outcome(a).contains("真实总成本仍未知"),"unknown should not be invalid or rank");
            ui(()->edit(a,"","pages","1800"));click(a,"worksheetApply");await(a,"worksheetJson","\"revision\": 5");
            check(outcome(a).contains("Brother HL-L1238W情景成本较低"),"basis recovery failed");
            log(out.resolve("J04-after.txt"),outcome(a)+"\n"+value(a,"worksheetJson"));
            System.out.println("PASS J04 native zero/blank/shared basis recovery");
            // Backend rejects extreme finite amount, leaves committed worksheet, allows retry.
            committed=value(a,"worksheetJson");log(out.resolve("J08-before.txt"),outcome(a)+"\n"+committed);
            ui(()->edit(a,"HP M232dw","hardware","1e1000000"));
            SwingUtilities.invokeLater(()->((JButton)field(a,"worksheetApply")).doClick());dismissWarning();
            check(committed.equals(value(a,"worksheetJson")),"invalid input replaced state");
            ui(()->edit(a,"HP M232dw","hardware","550"));click(a,"worksheetApply");await(a,"worksheetJson","\"revision\": 6");
            check(outcome(a).contains("Brother HL-L1238W情景成本较低"),"retry failed");
            log(out.resolve("J08-after.txt"),outcome(a)+"\n"+value(a,"worksheetJson"));
            System.out.println("PASS J08 native invalid finite cost and successful retry");
            // Changing region invalidates the old worksheet and removes controls.
            log(out.resolve("J10-before.txt"),outcome(a)+"\n"+value(a,"worksheetJson"));
            batch(a,"device_deployment_region:中国大陆北京市");await(a,"chatState","中国大陆北京市");
            ui(()->check(((Map<?,?>)field(a,"worksheetInputs")).isEmpty(),"stale cost fields still editable"));
            check(!outcome(a).contains("Brother HL-L1238W情景成本较低"),"stale cost winner leaked");
            log(out.resolve("J10-after.txt"),outcome(a)+"\n"+value(a,"chatReport"));
            System.out.println("PASS J10 native region change invalidates worksheet");

            System.out.println("WORKSHEET_NATIVE_PASS");
        } finally{ui(()->((JFrame)field(a,"frame")).dispose());}
    }
}
