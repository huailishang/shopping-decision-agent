import javax.swing.*;
import java.awt.*;
import java.io.*;
import java.nio.file.*;
import java.util.concurrent.TimeUnit;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.List;
import java.util.Base64;

/** H08 零第三方Java依赖桌面GUI。推荐结果来自已有Python decide()。 */
public final class ShoppingDecisionDesktop {
    private final JFrame frame = new JFrame("购物智能体｜打印机需求判断");
    private final CardLayout steps = new CardLayout();
    private final JPanel body = new JPanel(steps);
    private final JTextArea description = area(4), other = area(3), summary = area(12), result = area(15);
    private final JTextField pages = new JTextField(), budget = new JTextField(), idle = new JTextField();
    private final JComboBox<String> color = choices(), outsourced = choices(), wireless = choices(), scan = choices();
    private final JButton calculate = new JButton("确认并调用后端判断");
    private final JLabel status = new JLabel("仅本机运行，不下单、不查询实时价格。所有条件必须由用户确认。");
    private String lastReport = "";
    private final DesktopRequestGate requestGate = new DesktopRequestGate();
    private SwingWorker<Map<String,String>,Void> pendingWorker;
    private String[] captured;
    private final String python;

    private ShoppingDecisionDesktop(String python) {
        this.python = python;
        description.setText("");
        body.add(pageOne(), "one");
        body.add(pageTwo(), "two");
        body.add(pageThree(), "three");
        body.add(pageFour(), "four");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setLayout(new BorderLayout(12,12));
        JLabel title = new JLabel("  家用打印机决策 · H08 本机试用");
        title.setFont(title.getFont().deriveFont(Font.BOLD,20f));
        frame.add(title, BorderLayout.NORTH);
        frame.add(body, BorderLayout.CENTER);
        frame.add(status, BorderLayout.SOUTH);
        frame.setSize(750,690);
        frame.setLocationRelativeTo(null);
        frame.setVisible(true);
        show("one");
    }
    private static JTextArea area(int rows) { JTextArea a = new JTextArea(rows,55); a.setLineWrap(true); a.setWrapStyleWord(true); return a; }
    private static JComboBox<String> choices() { return new JComboBox<>(new String[]{"不确定","是","否"}); }
    private static JPanel vertical() { JPanel p = new JPanel(); p.setLayout(new BoxLayout(p, BoxLayout.Y_AXIS)); p.setBorder(BorderFactory.createEmptyBorder(18,24,18,24)); return p; }
    private static JPanel line(String label, JComponent field) { JPanel p=new JPanel(new BorderLayout(12,4)); p.setMaximumSize(new Dimension(700,65)); p.add(new JLabel(label),BorderLayout.WEST);p.add(field,BorderLayout.CENTER);return p; }
    private static JPanel buttons(JButton... buttons) { JPanel p=new JPanel(new FlowLayout(FlowLayout.LEFT));for(JButton b:buttons)p.add(b);return p; }
    private static JScrollPane scroll(JTextArea area) { JScrollPane p=new JScrollPane(area);p.setAlignmentX(Component.LEFT_ALIGNMENT);return p; }
    private void show(String id) { if (!id.equals("four") && !id.equals("three")) invalidatePending(); status.setText("本机 · 当前步骤："+id+" · 未连接购物交易平台");steps.show(body,id); }
    private JPanel pageOne() {
        JPanel p=vertical();p.add(new JLabel("第一步 · 一句话说明打印机需求（不会自动猜测条件）"));p.add(scroll(description));
        JButton next=new JButton("下一步：补充条件");next.addActionListener(e->{if(description.getText().isBlank())error("请先填写需求");else show("two");});p.add(buttons(next));return p;
    }
    private JPanel pageTwo() {
        JPanel p=vertical();p.add(new JLabel("第二步 · 不确定请留空或选“不确定”"));
        p.add(line("每月张数（可填50或0–50）",pages));p.add(line("预算上限（元）",budget));p.add(line("连续闲置周数",idle));
        p.add(line("需要彩印",color));p.add(line("接受外包彩印",outsourced));p.add(line("需要无线/手机打印",wireless));p.add(line("需要扫描",scan));
        p.add(new JLabel("其他硬要求（微信打印不等于普通Wi-Fi），每行一条"));p.add(scroll(other));
        JButton back=new JButton("返回原话"),next=new JButton("核对我的理解");back.addActionListener(e->show("one"));next.addActionListener(e->review());p.add(buttons(back,next));return p;
    }
    private String number(JTextField f,String label) {String s=f.getText().trim();if(!s.isEmpty()){try {long v=Long.parseLong(s);if(v<0||v>1000000)throw new NumberFormatException();}catch(NumberFormatException e){throw new IllegalArgumentException(label+"：请输入0至1000000的整数或留空");}}return s;}
    private String printVolume() {
        String s=pages.getText().trim();
        if(s.isEmpty())return s;
        if(s.matches("[0-9]+"))return number(pages,"每月张数");
        if(!s.matches("[0-9]+\\s*[-–~至]\\s*[0-9]+"))throw new IllegalArgumentException("每月张数：请填非负整数或0–50这样的范围");
        String[] bounds=s.split("\\s*[-–~至]\\s*");
        try {
            long lo=Long.parseLong(bounds[0]),hi=Long.parseLong(bounds[1]);
            if(lo>hi || hi>1000000)throw new NumberFormatException();
        }catch(NumberFormatException e){throw new IllegalArgumentException("每月张数：范围下界不得超过上界，且不能超过1000000");}
        return s;
    }
    private static String bool(JComboBox<String> b) {int i=b.getSelectedIndex();return i==0?"":i==1?"true":"false";}
    private String[] gather() {return new String[]{description.getText().trim(),printVolume(),number(budget,"预算"),number(idle,"闲置周数"),bool(color),bool(outsourced),bool(wireless),bool(scan),other.getText().trim()};}
    private void review() {try {invalidatePending();captured=gather();lastReport="";result.setText("");
        summary.setText("第三步 · 请确认整理后的条件（未知不代表否）\n\n原始需求："+captured[0]+"\n每月张数："+display(captured[1])+"\n预算："+display(captured[2])+"\n闲置周数："+display(captured[3])+"\n彩印："+display(captured[4])+"\n外包彩印："+display(captured[5])+"\n无线："+display(captured[6])+"\n扫描："+display(captured[7])+"\n待核对原话与其他要求：\n"+captured[0]+"\n"+captured[8]);show("three");
    }catch(IllegalArgumentException ex){error(ex.getMessage());}}
    private static String display(String s) {return s.isEmpty()?"未知":s.equals("true")?"是":s.equals("false")?"否":s;}
    private JPanel pageThree() { JPanel p=vertical();summary.setEditable(false);p.add(scroll(summary));JButton back=new JButton("修改条件");back.addActionListener(e->show("two"));calculate.addActionListener(e->calculate());p.add(buttons(back,calculate));return p; }
    private JPanel pageFour() {JPanel p=vertical();result.setEditable(false);p.add(scroll(result));JButton edit=new JButton("修改后重新判断"),preview=new JButton("预览本地评审记录");edit.addActionListener(e->{lastReport="";result.setText("");show("two");});preview.addActionListener(e->previewReport());p.add(buttons(edit,preview));return p; }
    private void previewReport() {
        JTextArea editor = area(18);
        editor.setText(lastReport + "\n\n人工评审意见（请自行填写）：\n");
        int choice = JOptionPane.showConfirmDialog(frame, new JScrollPane(editor),
                "预览并编辑评审记录（默认不保存）", JOptionPane.OK_CANCEL_OPTION);
        if (choice != JOptionPane.OK_OPTION) return;
        JFileChooser chooser = new JFileChooser();
        chooser.setSelectedFile(new File("H09_人工评审记录.txt"));
        if (chooser.showSaveDialog(frame) == JFileChooser.APPROVE_OPTION) {
            try { Files.writeString(chooser.getSelectedFile().toPath(), editor.getText(), StandardCharsets.UTF_8,
                    StandardOpenOption.CREATE_NEW); }
            catch (IOException ex) { error("保存失败（不覆盖现有文件）：" + ex.getMessage()); }
        }
    }
    private void invalidatePending() {
        requestGate.invalidate();
        if (pendingWorker != null && !pendingWorker.isDone()) pendingWorker.cancel(true);
        pendingWorker = null;
        calculate.setEnabled(true);
    }
    private void calculate() {
        calculate.setEnabled(false);status.setText("正在调用本机Python决策器...");
        final String[] snapshot=captured.clone();
        final String confirmedSummary=summary.getText();
        final long version=requestGate.next();
        SwingWorker<Map<String,String>,Void> worker = new SwingWorker<Map<String,String>,Void>() {
            protected Map<String,String> doInBackground() throws Exception {
                List<String> cmd=new ArrayList<>();cmd.add(python);cmd.add("-m");cmd.add("shopping_decision.desktop_bridge");
                for(String s:snapshot)cmd.add(Base64.getEncoder().encodeToString(s.getBytes(StandardCharsets.UTF_8)));
                return DesktopBridgeClient.invoke(new ProcessBuilder(cmd), 20_000);
            }
            protected void done() {if (!requestGate.accepts(version)) return;calculate.setEnabled(true);pendingWorker=null;try {Map<String,String> data=get();if(data.containsKey("error"))throw new Exception(data.get("error"));
                lastReport="确认条件：\n"+confirmedSummary+"\n\n完整后端审计记录（包含引用、拒绝理由、来源日期、版本）：\n"+data.getOrDefault("report_json","未提供完整记录")+"\n\n人工评审状态：未完成";
                String userStatus = switch(data.get("status")) {
                    case "clarify" -> "还需要确认条件";
                    case "defer" -> "证据不足，暂缓推荐";
                    case "compare_routes" -> "建议比较不同路线";
                    case "route_recommended" -> "有条件的技术路线建议";
                    case "invalid" -> "输入不符合要求";
                    default -> "暂不能作出判断";
                };
                result.setText("第四步 · 本机判断\n\n状态："+userStatus+"\n\n理由：\n"+data.get("reasons")+"\n\n需要澄清：\n"+data.get("questions")+"\n\n未核实：\n"+data.get("unknowns")+"\n\n可用于决策的证据：\n"+(data.get("evidence").isBlank()?"无已通过用途及范围审核的决策证据；当前来源仅可作研究线索":data.get("evidence"))+"\n\n暂不提供现售型号、报价、加购或付款。");show("four");
            } catch(Exception ex) {error("后端错误，可重试："+ex.getMessage());}}
        };
        pendingWorker=worker;
        worker.execute();
    }
    private void error(String msg) {JOptionPane.showMessageDialog(frame,msg,"请检查",JOptionPane.WARNING_MESSAGE);status.setText(msg);}
    public static void main(String[] args) {String python=args.length>0?args[0]:(System.getProperty("os.name").toLowerCase().contains("win")?"python":"python3");SwingUtilities.invokeLater(()->new ShoppingDecisionDesktop(python));}
}
