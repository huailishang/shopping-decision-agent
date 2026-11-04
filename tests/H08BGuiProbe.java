import javax.swing.*;
import java.awt.*;
import java.awt.image.BufferedImage;
import javax.imageio.ImageIO;
import java.io.File;
import java.lang.reflect.*;
import java.nio.file.*;

/** H08 B 自动化实际Swing操作：代录真人需求，非真人本人点击，也非独立评估。 */
public final class H08BGuiProbe {
    static Object app;
    static JFrame frame;
    static Object get(String name) throws Exception {
        Field f=ShoppingDecisionDesktop.class.getDeclaredField(name);
        f.setAccessible(true);
        return f.get(app);
    }
    static JButton findButton(Container root,String text) {
        for(Component c:root.getComponents()){
            if(c instanceof JButton b && b.getText().equals(text))return b;
            if(c instanceof Container p){JButton found=findButton(p,text);if(found!=null)return found;}
        }
        return null;
    }
    static void edt(Runnable work) throws Exception {SwingUtilities.invokeAndWait(work);}
    static String waitResult(String token) throws Exception {
        for(int i=0;i<150;i++){
            final String[] value=new String[1];
            edt(()->{try{value[0]=((JTextArea)get("result")).getText();}catch(Exception e){throw new RuntimeException(e);}});
            if(value[0]!=null && value[0].contains(token))return value[0];
            Thread.sleep(100);
        }
        throw new IllegalStateException("结果超时或不含 "+token);
    }
    static void screenshot(String path) throws Exception {
        // WSLg 的真实屏幕捕获可能只得到空白；采用已展示Swing窗口的组件渲染快照。
        // 此产物是 GUI 渲染记录，不能冒充操作系统级真实屏幕截图。
        final BufferedImage[] capture=new BufferedImage[1];
        edt(()->{
            BufferedImage image=new BufferedImage(frame.getWidth(),frame.getHeight(),BufferedImage.TYPE_INT_RGB);
            Graphics2D graphics=image.createGraphics();
            frame.paintAll(graphics);
            graphics.dispose();
            capture[0]=image;
        });
        ImageIO.write(capture[0],"png",new File(path));
    }
    static <T extends Component> T findPart(Container root,Class<T> type){
        for(Component child:root.getComponents()){
            if(type.isInstance(child))return type.cast(child);
            if(child instanceof Container container){T nested=findPart(container,type);if(nested!=null)return nested;}
        }
        return null;
    }
    static JDialog activeDialog(boolean withChooser) throws Exception {
        for(int i=0;i<60;i++){
            final JDialog[] found=new JDialog[1];
            edt(()->{for(Window window:Window.getWindows()){
                if(window instanceof JDialog dlg && dlg.isShowing() && dlg.getOwner()==frame){
                    boolean hasChooser=findPart(dlg.getContentPane(),JFileChooser.class)!=null;
                    if(hasChooser==withChooser){found[0]=dlg;break;}
                }
            }});
            if(found[0]!=null)return found[0];
            Thread.sleep(100);
        }
        throw new IllegalStateException("未找到预览/保存对话框 "+withChooser);
    }
    static void saveViaActualGui(String path) throws Exception {
        SwingUtilities.invokeLater(()->findButton(frame,"预览本地评审记录").doClick());
        JDialog preview=activeDialog(false);
        edt(()->{
            JTextArea editor=findPart(preview.getContentPane(),JTextArea.class);
            if(editor==null || !editor.getText().contains("0–50"))
                throw new IllegalStateException("保存预览缺失0–50范围");
            JButton ok=preview.getRootPane().getDefaultButton();
            if(ok==null)throw new IllegalStateException("预览确认按钮缺失");
            ok.doClick();
        });
        JDialog save=activeDialog(true);
        edt(()->{
            JFileChooser chooser=findPart(save.getContentPane(),JFileChooser.class);
            chooser.setSelectedFile(new File(path));
            chooser.approveSelection();
        });
        for(int i=0;i<50;i++){
            if(Files.exists(Path.of(path))) {
                String body=Files.readString(Path.of(path));
                if(!body.contains("monthly_pages_range") || !body.contains("0–50"))
                    throw new IllegalStateException("保存文件缺少结构化区间");
                System.out.println("PASS actual Swing preview/edit/save: "+path+", chars="+body.length());
                return;
            }
            Thread.sleep(100);
        }
        throw new IllegalStateException("未见保存的用户审计文件");
    }
    public static void main(String[] args) throws Exception {
        final String python=args.length>0?args[0]:"python3";
        try {
            edt(()->{
                try {
                    Constructor<ShoppingDecisionDesktop> c=ShoppingDecisionDesktop.class.getDeclaredConstructor(String.class);
                    c.setAccessible(true);app=c.newInstance(python);
                    frame=(JFrame)get("frame");
                    ((JTextArea)get("description")).setText("预算千元内，每月打印0–50页；家里只需要黑白，偶尔彩印可以去店里；希望支持微信打印、可靠耐用，重点比较兄弟和惠普");
                    findButton(frame,"下一步：补充条件").doClick();
                    ((JTextField)get("pages")).setText("0–50");
                    ((JTextField)get("budget")).setText("1000");
                    ((JComboBox<?>)get("color")).setSelectedIndex(2);
                    ((JComboBox<?>)get("outsourced")).setSelectedIndex(1);
                    ((JTextArea)get("other")).setText("希望支持微信小程序打印（不等同普通Wi-Fi）\n可靠耐用、兄弟和惠普优先");
                    findButton(frame,"核对我的理解").doClick();
                    String summary=((JTextArea)get("summary")).getText();
                    if(!summary.contains("0–50"))throw new IllegalStateException("范围没有出现在需求确认页");
                    findButton(frame,"确认并调用后端判断").doClick();
                }catch(Exception e){throw new RuntimeException(e);}
            });
            String actual=waitResult("证据不足，暂缓推荐");
            if(!actual.contains("0–50") || !actual.contains("微信"))throw new IllegalStateException("后端结果漏掉区间或微信需求");
            screenshot("reports/h08_b_gui_range_real_input.png");
            System.out.println("PASS real Swing case: range 0–50, wechat requirement, defer without invented evidence");
            saveViaActualGui("data/private/h08_b_real_user_range_audit_20261102_v2.txt");
            edt(()->{
                try {
                    findButton(frame,"修改后重新判断").doClick();
                    ((JTextField)get("pages")).setText("50–200");
                    ((JComboBox<?>)get("color")).setSelectedIndex(1);
                    ((JComboBox<?>)get("outsourced")).setSelectedIndex(2);
                    findButton(frame,"核对我的理解").doClick();
                    findButton(frame,"确认并调用后端判断").doClick();
                }catch(Exception e){throw new RuntimeException(e);}
            });
            String changed=waitResult("还需要确认条件");
            if(!changed.contains("颜色要求"))throw new IllegalStateException("修改后未触发颜色冲突");
            screenshot("reports/h08_b_gui_range_changed.png");
            System.out.println("PASS real Swing changed request: old result invalidated, color conflict clarified");
            edt(()->frame.dispose());
            System.out.println("H08 B Swing automated probe: 2/2 PASS (not human-click independent acceptance)");
        } finally {if(frame!=null)edt(()->frame.dispose());}
    }
}
