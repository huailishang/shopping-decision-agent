import javax.swing.*;
import javax.swing.filechooser.FileNameExtensionFilter;
import java.awt.*;
import java.io.*;
import java.nio.file.*;
import java.util.concurrent.TimeUnit;
import java.nio.charset.StandardCharsets;
import java.net.URI;
import java.net.URLEncoder;
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
    private final JComboBox<String> wechatRequired = choices(), autoDuplex = choices();
    private final JComboBox<String> wechatWorkflow = new JComboBox<>(new String[]{"待确认", "微信小程序直接打印", "文件转存到厂商App后打印"});
    private final JComboBox<String> budgetScope = new JComboBox<>(new String[]{"待确认", "主机含运费及必要支出", "还包括本次额外购买的耗材"});
    private final JTextField deliveryRegion = new JTextField();
    private final JTextField deviceDeploymentRegion = new JTextField();
    private Path hainaMcpReport = null;
    private final JLabel hainaMcpReportStatus = new JLabel("未选择；普通判断不会读取海纳文件");
    private final JButton calculate = new JButton("确认并调用后端判断");
    private final JLabel status = new JLabel("仅本机运行，不下单、不查询实时价格。所有条件必须由用户确认。");
    private String lastReport = "";
    private final DesktopRequestGate requestGate = new DesktopRequestGate();
    private SwingWorker<Map<String,String>,Void> pendingWorker;
    private String[] captured;
    private final String python;
    // 新对话入口与旧表单共用后端和请求版本保护；参考按钮只编辑草稿。
    private final JTextArea chatTranscript = area(15), chatInput = area(3);
    private final JTextArea chatUnderstanding = area(10), chatOutcome = area(12);
    private final JLabel chatPrompt = new JLabel("正在加载本机问题...");
    private final JPanel chatReferences = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 4));
    private final JPanel chatEdits = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 4));
    private final JButton chatSend = new JButton("发送并确认"), chatPreview = new JButton("预览/另存审计");
    private String chatState = "", chatPromptField = "", chatReport = "";
    private SwingWorker<Map<String,String>,Void> chatWorker;

    private ShoppingDecisionDesktop(String python) {
        this.python = python;
        description.setText("");
        body.add(chatPage(), "chat");
        body.add(pageOne(), "one");
        body.add(pageTwo(), "two");
        body.add(pageThree(), "three");
        body.add(pageFour(), "four");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setLayout(new BorderLayout(12,12));
        JLabel title = new JLabel("  购物智能体 · 对话需求判断（本机只读）");
        title.setFont(title.getFont().deriveFont(Font.BOLD,20f));
        frame.add(title, BorderLayout.NORTH);
        frame.add(body, BorderLayout.CENTER);
        frame.add(status, BorderLayout.SOUTH);
        frame.setSize(850,850);
        frame.setLocationRelativeTo(null);
        frame.setVisible(true);
        show("chat");
        updateChat("", "", "");
    }
    /** 新主入口：参考答案只填文本，不进入后端；发送后才更新显式条件。 */
    private JPanel chatPage() {
        JPanel panel = new JPanel(new BorderLayout(8, 8));
        panel.setBorder(BorderFactory.createEmptyBorder(12, 16, 12, 16));
        chatTranscript.setEditable(false);
        chatUnderstanding.setEditable(false);
        chatOutcome.setEditable(false);
        chatTranscript.setText("助手：请先明确商品品类。这里不会自动替你确认默认值，也不会查询或购买商品。\n");
        JTabbedPane details = new JTabbedPane();
        JPanel understandingPanel = new JPanel(new BorderLayout(4, 4));
        understandingPanel.add(new JScrollPane(chatUnderstanding), BorderLayout.CENTER);
        JPanel edits = new JPanel(new BorderLayout());
        edits.add(new JLabel("已确认/待补条件：点击字段可修改，发送才生效"), BorderLayout.NORTH);
        chatEdits.setLayout(new FlowLayout(FlowLayout.LEFT, 4, 2));
        edits.add(new JScrollPane(chatEdits), BorderLayout.CENTER);
        edits.setPreferredSize(new Dimension(300, 125));
        understandingPanel.add(edits, BorderLayout.SOUTH);
        details.addTab("目前理解/修改", understandingPanel);
        details.addTab("证据与下一步", new JScrollPane(chatOutcome));
        JSplitPane split = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT,
                new JScrollPane(chatTranscript), details);
        split.setResizeWeight(0.58);
        panel.add(split, BorderLayout.CENTER);

        JPanel inputArea = new JPanel(new BorderLayout(4, 4));
        JPanel promptPanel = new JPanel(new BorderLayout(4, 4));
        promptPanel.add(chatPrompt, BorderLayout.NORTH);
        chatReferences.setLayout(new FlowLayout(FlowLayout.LEFT, 4, 2));
        promptPanel.add(new JScrollPane(chatReferences), BorderLayout.CENTER);
        promptPanel.setPreferredSize(new Dimension(700, 96));
        inputArea.add(promptPanel, BorderLayout.NORTH);
        inputArea.add(new JScrollPane(chatInput), BorderLayout.CENTER);
        JPanel actions = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 2));
        chatSend.addActionListener(e -> {
            String text = chatInput.getText().trim();
            if (chatPromptField.isBlank() || text.isBlank()) {
                error("请先选择当前问题并填写明确答复；“暂不确定”也可发送");
            } else {
                updateChat(chatPromptField, text, chatPrompt.getText());
            }
        });
        chatPreview.addActionListener(e -> {
            if (chatReport.isBlank()) {
                error("当前没有可预览的会话审计");
            } else {
                lastReport = chatReport;
                previewReport();
            }
        });
        JButton newSession = new JButton("新建空白会话");
        newSession.addActionListener(e -> {
            requestGate.invalidate();
            if (chatWorker != null && !chatWorker.isDone()) chatWorker.cancel(true);
            chatState = "";
            chatPromptField = "";
            chatReport = "";
            chatInput.setText("");
            chatTranscript.setText("助手：已开启空白会话。原会话不会自动带入；没有保存到磁盘。\n");
            chatSend.setEnabled(true);
            updateChat("", "", "");
        });
        JButton oldForm = new JButton("旧表单回退（实验）");
        oldForm.addActionListener(e -> show("one"));
        JButton bulk = new JButton("批量补充/修改");
        bulk.addActionListener(e -> {
            requestGate.invalidate();
            if (chatWorker != null && !chatWorker.isDone()) chatWorker.cancel(true);
            chatSend.setEnabled(true);
            chatPromptField = "batch";
            chatPrompt.setText("批量答复：每行“字段名：答案”，最多8行；只有发送才确认。");
            chatReferences.removeAll();
            chatReferences.revalidate();
            chatReferences.repaint();
            chatInput.setText("");
            chatInput.requestFocusInWindow();
        });
        actions.add(chatSend);
        actions.add(bulk);
        actions.add(chatPreview);
        actions.add(newSession);
        actions.add(oldForm);
        inputArea.add(actions, BorderLayout.SOUTH);
        inputArea.setPreferredSize(new Dimension(700, 255));
        panel.add(inputArea, BorderLayout.SOUTH);
        return panel;
    }

    /** 所有轮次走统一Python受控规则与现有Web共享研究；Java不解析自由文字。 */
    private void updateChat(String field, String submitted, String previousPrompt) {
        if (chatWorker != null && !chatWorker.isDone()) chatWorker.cancel(true);
        final String snapshot = chatState;
        final String changedField = field;
        final String raw = submitted;
        final long version = requestGate.next();
        chatSend.setEnabled(false);
        status.setText("本机正在核对本轮显式答复；不会自动访问商城...");
        SwingWorker<Map<String,String>,Void> worker = new SwingWorker<Map<String,String>,Void>() {
            @Override protected Map<String,String> doInBackground() throws Exception {
                List<String> cmd = new ArrayList<>();
                cmd.add(python);
                cmd.add("-m");
                cmd.add("shopping_decision.chat_bridge");
                for (String value : new String[]{snapshot, changedField, raw}) {
                    cmd.add(Base64.getEncoder().encodeToString(value.getBytes(StandardCharsets.UTF_8)));
                }
                return DesktopBridgeClient.invoke(new ProcessBuilder(cmd), 20_000);
            }
            @Override protected void done() {
                if (!requestGate.accepts(version)) return;
                chatWorker = null;
                chatSend.setEnabled(true);
                try {
                    Map<String,String> out = get();
                    if (out.containsKey("error")) throw new IllegalArgumentException(out.get("error"));
                    if (!out.containsKey("state_json") || !out.containsKey("report_json")) {
                        throw new IllegalArgumentException("对话结果缺少版本/审计");
                    }
                    chatState = out.get("state_json");
                    chatReport = out.get("report_json");
                    if (!raw.isBlank()) {
                        chatTranscript.append("\n用户（" + previousPrompt + "）：" + raw + "\n");
                    }
                    chatPromptField = out.getOrDefault("prompt_field", "");
                    String next = out.getOrDefault("prompt", "本轮已完成");
                    chatPrompt.setText(next.length() > 80 ? next.substring(0, 80) + "…" : next);
                    chatTranscript.append("助手：" + next + "\n");
                    chatTranscript.setCaretPosition(chatTranscript.getDocument().getLength());
                    chatUnderstanding.setText(out.getOrDefault("understanding", ""));
                    chatUnderstanding.setCaretPosition(0);
                    chatOutcome.setText(out.getOrDefault("result_text", ""));
                    chatOutcome.setCaretPosition(0);
                    chatInput.setText("");
                    chatReferences.removeAll();
                    for (String row : out.getOrDefault("choices", "").split("\\R")) {
                        if (row.isBlank()) continue;
                        String[] items = row.split("\\t", 2);
                        if (items.length != 2) continue;
                        JButton reference = new JButton(items[0]);
                        // 不调用 updateChat：点击参考答案仅把草稿送入可编辑文本框。
                        reference.addActionListener(e -> { chatInput.setText(items[1]); chatInput.requestFocusInWindow(); });
                        chatReferences.add(reference);
                    }
                    chatReferences.revalidate();
                    chatReferences.repaint();
                    chatEdits.removeAll();
                    for (String row : out.getOrDefault("editable", "").split("\\R")) {
                        String[] items = row.split("\\t", 3);
                        if (items.length < 3) continue;
                        JButton edit = new JButton(items[1]);
                        edit.addActionListener(e -> {
                            requestGate.invalidate();
                            if (chatWorker != null && !chatWorker.isDone()) chatWorker.cancel(true);
                            chatSend.setEnabled(true);
                            chatPromptField = items[0];
                            chatPrompt.setText("修改 " + items[1] + "（当前值：" + items[2] + "；发送后才生效）");
                            chatInput.setText("");
                            chatInput.requestFocusInWindow();
                        });
                        chatEdits.add(edit);
                    }
                    chatEdits.revalidate();
                    chatEdits.repaint();
                    status.setText("对话版本 " + out.getOrDefault("session_version", "0")
                            + " · 本机只读研究 · 不批准购买/交易");
                } catch (Exception ex) {
                    status.setText("本轮未确认，原条件保留：" + ex.getMessage());
                    JOptionPane.showMessageDialog(frame, "本轮答复未保存：" + ex.getMessage(),
                            "请检查", JOptionPane.WARNING_MESSAGE);
                }
            }
        };
        chatWorker = worker;
        worker.execute();
    }
    private static JTextArea area(int rows) { JTextArea a = new JTextArea(rows,55); a.setLineWrap(true); a.setWrapStyleWord(true); return a; }
    private static JComboBox<String> choices() { return new JComboBox<>(new String[]{"不确定","是","否"}); }
    private static JPanel vertical() { JPanel p = new JPanel(); p.setLayout(new BoxLayout(p, BoxLayout.Y_AXIS)); p.setBorder(BorderFactory.createEmptyBorder(18,24,18,24)); return p; }
    private static JPanel line(String label, JComponent field) { JPanel p=new JPanel(new BorderLayout(12,4)); p.setAlignmentX(Component.LEFT_ALIGNMENT); p.setMaximumSize(new Dimension(700,65)); p.add(new JLabel(label),BorderLayout.WEST);p.add(field,BorderLayout.CENTER);return p; }
    private static JPanel buttons(JButton... buttons) { JPanel p=new JPanel(new FlowLayout(FlowLayout.LEFT));p.setAlignmentX(Component.LEFT_ALIGNMENT);for(JButton b:buttons)p.add(b);return p; }
    private static JScrollPane scroll(JTextArea area) { JScrollPane p=new JScrollPane(area);p.setAlignmentX(Component.LEFT_ALIGNMENT);return p; }
    private void show(String id) { if (!id.equals("four") && !id.equals("three")) invalidatePending(); status.setText("本机 · 当前步骤："+id+" · 未连接购物交易平台");steps.show(body,id); }
    private JPanel pageOne() {
        JPanel p=vertical();p.add(new JLabel("第一步 · 一句话说明打印机需求（不会自动猜测条件）"));p.add(scroll(description));
        JButton next=new JButton("下一步：补充条件");next.addActionListener(e->{if(description.getText().isBlank())error("请先填写需求");else show("two");});
        JButton discovery = new JButton("京东 / 淘宝商品发现（只读实验）");discovery.addActionListener(e->openMarketplaceTool());
        JButton chat = new JButton("返回对话主入口");chat.addActionListener(e->show("chat"));
        p.add(buttons(next,discovery,chat));return p;
    }
    private JPanel pageTwo() {
        JPanel p=vertical();p.add(new JLabel("第二步 · 不确定请留空或选“不确定”"));
        p.add(line("每月张数（可填50或0–50）",pages));p.add(line("预算上限（元）",budget));p.add(line("连续闲置周数",idle));
        p.add(line("需要彩印",color));p.add(line("接受外包彩印",outsourced));p.add(line("需要无线/手机打印",wireless));p.add(line("需要扫描",scan));
        p.add(line("微信打印是必须条件",wechatRequired));p.add(line("可接受的微信方式",wechatWorkflow));
        p.add(line("必须自动双面打印",autoDuplex));p.add(line("预算支出口径",budgetScope));
        p.add(line("收货省市区（未知留空，无需详细地址）",deliveryRegion));
        p.add(line("设备实际部署国家/地区（与收货地可能不同）",deviceDeploymentRegion));
        p.add(new JLabel("其他硬要求（微信打印不等于普通Wi-Fi），每行一条"));p.add(scroll(other));
        JButton back=new JButton("返回原话"),next=new JButton("核对我的理解");back.addActionListener(e->show("one"));next.addActionListener(e->review());p.add(buttons(back,next));
        JPanel wrapper = new JPanel(new BorderLayout());wrapper.add(new JScrollPane(p), BorderLayout.CENTER);return wrapper;
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
    private String[] gather() {return new String[]{description.getText().trim(),printVolume(),number(budget,"预算"),number(idle,"闲置周数"),bool(color),bool(outsourced),bool(wireless),bool(scan),other.getText().trim(),bool(wechatRequired),new String[]{"unknown","miniprogram","transfer_to_app"}[wechatWorkflow.getSelectedIndex()],bool(autoDuplex),deliveryRegion.getText().trim(),new String[]{"unknown","device_delivered","device_and_extra_consumables"}[budgetScope.getSelectedIndex()],deviceDeploymentRegion.getText().trim()};}
    private void review() {try {invalidatePending();captured=gather();lastReport="";result.setText("");
        summary.setText("第三步 · 请确认整理后的条件（未知不代表否）\n\n原始需求："+captured[0]+"\n每月张数："+display(captured[1])+"\n预算："+display(captured[2])+"\n闲置周数："+display(captured[3])+"\n彩印："+display(captured[4])+"\n外包彩印："+display(captured[5])+"\n无线："+display(captured[6])+"\n扫描："+display(captured[7])+"\n微信是必须条件："+display(captured[9])+"\n微信方式："+wechatWorkflow.getSelectedItem()+"\n必须自动双面："+display(captured[11])+"\n收货地区："+display(captured[12])+"\n设备实际部署地区："+display(captured[14])+"\n预算口径："+budgetScope.getSelectedItem()+"\n待核对原话与其他要求：\n"+captured[0]+"\n"+captured[8]);show("three");
    }catch(IllegalArgumentException ex){error(ex.getMessage());}}
    private static String display(String s) {return s.isEmpty()?"未知":s.equals("true")?"是":s.equals("false")?"否":s;}
    private JPanel pageThree() {
        JPanel p=vertical();
        summary.setEditable(false);
        p.add(scroll(summary));
        p.add(new JLabel("可选：只加载本机海纳MCP合成测试报告，不会联网。真实响应在用途许可核准前会被阻断。"));
        p.add(hainaMcpReportStatus);
        JButton chooseResearch = new JButton("选择本机合成测试报告");
        JButton clearResearch = new JButton("清除研究材料");
        chooseResearch.addActionListener(e -> chooseHainaMcpReport());
        clearResearch.addActionListener(e -> {
            hainaMcpReport = null;
            hainaMcpReportStatus.setText("未选择；普通判断不会读取海纳文件");
        });
        JButton back=new JButton("修改条件");
        back.addActionListener(e->show("two"));
        calculate.addActionListener(e->calculate());
        p.add(buttons(chooseResearch, clearResearch));
        p.add(buttons(back,calculate));
        return p;
    }

    private void chooseHainaMcpReport() {
        Path expected = Path.of("tests", "fixtures", "haina_mcp_synthetic_bundle.json")
                .toAbsolutePath().normalize();
        JFileChooser chooser = new JFileChooser(expected.getParent().toFile());
        chooser.setDialogTitle("选择仓库内固定哈希的海纳MCP合成测试夹具");
        chooser.setFileFilter(new FileNameExtensionFilter("固定合成测试包 (haina_mcp_synthetic_bundle.json)", "json"));
        chooser.setSelectedFile(expected.toFile());
        if (chooser.showOpenDialog(frame) != JFileChooser.APPROVE_OPTION) return;
        Path chosen = chooser.getSelectedFile().toPath().toAbsolutePath().normalize();
        try {
            if (!chosen.equals(expected)) {
                throw new IOException("只允许加载仓库内固定哈希的tests/fixtures/haina_mcp_synthetic_bundle.json；任意文件即使自标synthetic_test也会被阻断");
            }
            long size = Files.size(chosen);
            if (size < 1 || size > 200_000) throw new IOException("文件大小必须在1至200000字节之间");
            hainaMcpReport = chosen;
            hainaMcpReportStatus.setText("已选择固定哈希夹具：" + chosen.getFileName()
                    + "；仅作接线测试，不代表真实商品证据");
        } catch (IOException ex) {
            error("无法选择本机研究材料：" + ex.getMessage());
        }
    }
    private JPanel pageFour() {JPanel p=vertical();result.setEditable(false);p.add(scroll(result));JButton edit=new JButton("修改后重新判断"),preview=new JButton("预览本地评审记录");edit.addActionListener(e->{lastReport="";result.setText("");show("two");});preview.addActionListener(e->previewReport());JButton discovery=new JButton("打开京东 / 淘宝商品发现（只读）");discovery.addActionListener(e->openMarketplaceTool());p.add(buttons(edit,preview,discovery));return p; }
    /** 只构造官方商品搜索页 URL；实际打开必须由用户点击，绝不传输账号登录信息。 */
    static URI marketplaceSearchUri(String query) {
        return marketplaceSearchUri(query, "jd");
    }
    static URI marketplaceSearchUri(String query, String platform) {
        if (query == null || query.isBlank() || query.length() > 100
                || query.chars().anyMatch(c -> c < 32 || c == 127)) {
            throw new IllegalArgumentException("搜索词必须为1至100字且不含控制字符");
        }
        String base = switch (platform) {
            case "jd" -> "https://search.jd.com/Search?keyword=";
            case "taobao" -> "https://s.taobao.com/search?q=";
            default -> throw new IllegalArgumentException("不支持的商城");
        };
        return URI.create(base + URLEncoder.encode(query.trim(), StandardCharsets.UTF_8));
    }

    /** 独立商品发现窗口，不影响打印机需求与购买批准的状态。 */
    private void openMarketplaceTool() {
        JDialog dialog = new JDialog(frame, "京东 / 淘宝商品发现｜用户自选商品｜只读", false);
        dialog.setDefaultCloseOperation(WindowConstants.DISPOSE_ON_CLOSE);
        JPanel p = vertical();
        p.add(new JLabel("输入搜索词 → 自己选择京东或淘宝并登录 → 粘贴1～5条商品详情链接"));
        JComboBox<String> marketplace = new JComboBox<>(new String[]{"京东", "淘宝 / 天猫"});
        p.add(line("选择商城", marketplace));
        JTextField keyword = new JTextField(description.getText().isBlank()
                ? "" : description.getText().trim().substring(0, Math.min(100, description.getText().trim().length())));
        p.add(line("商品搜索词", keyword));
        JLabel linkHelp = new JLabel("完整商品链接：京东 item.jd.com/数字.html；淘宝 item.taobao.com/item.htm?id=数字");
        p.add(linkHelp);
        p.add(new JLabel("每行一个链接，不填写账号和密码，不接受需跳转的短链接"));
        JTextArea links = area(6);p.add(scroll(links));
        p.add(new JLabel("核验记录（仅为商品线索，不能证明价格、库存或型号）"));
        JTextArea outcome = area(11);outcome.setEditable(false);p.add(scroll(outcome));
        JButton open = new JButton("打开选中商城搜索");
        JButton review = new JButton("校验粘贴的链接（不联网）");
        JComboBox<String> verifiedLinks = new JComboBox<>();
        JButton openVerified = new JButton("打开已校验商品链接");
        openVerified.setEnabled(false);
        p.add(line("校验通过的商品（仅网址）", verifiedLinks));
        marketplace.addActionListener(e -> {
            verifiedLinks.removeAllItems();
            openVerified.setEnabled(false);
        });
        JButton close = new JButton("关闭");
        open.addActionListener(e -> {
            try {
                String site = marketplace.getSelectedIndex() == 0 ? "jd" : "taobao";
                URI destination = marketplaceSearchUri(keyword.getText(), site);
                if (!Desktop.isDesktopSupported() || !Desktop.getDesktop().isSupported(Desktop.Action.BROWSE)) {
                    throw new IllegalStateException("当前系统不支持打开默认浏览器");
                }
                Desktop.getDesktop().browse(destination);
                outcome.setText("浏览器已尝试打开所选商城的搜索页。请自行决定是否登录并手动复制商品链接。\n"
                        + "本机购物智能体不读取 Cookie、登录状态、商品页内容或支付信息。");
            } catch (Exception ex) {
                JOptionPane.showMessageDialog(dialog, "无法打开浏览器：" + ex.getMessage(),
                        "浏览器未打开", JOptionPane.WARNING_MESSAGE);
            }
        });
        review.addActionListener(e -> {
            try {
                // 与 Python 校验一致，拒绝模糊/过长搜索词，避免用户误以为打开了不可信站点。
                String site = marketplace.getSelectedIndex() == 0 ? "jd" : "taobao";
                marketplaceSearchUri(keyword.getText(), site);
                String rawLinks = links.getText();
                if (rawLinks.isBlank() || rawLinks.length() > 12000) {
                    throw new IllegalArgumentException("请粘贴1至5条当前商城的完整商品详情链接");
                }
                final String query = keyword.getText().trim();
                final String chosenPlatform = site;
                verifiedLinks.removeAllItems();
                openVerified.setEnabled(false);
                review.setEnabled(false);
                outcome.setText("仅本机校验用户选取的商品链接，不会访问外部 API ...");
                SwingWorker<Map<String,String>,Void> worker = new SwingWorker<Map<String,String>,Void>() {
                    @Override protected Map<String,String> doInBackground() throws Exception {
                        List<String> cmd = new ArrayList<>();
                        cmd.add(python);cmd.add("-m");cmd.add("shopping_decision.discovery_bridge");
                        cmd.add(Base64.getEncoder().encodeToString(query.getBytes(StandardCharsets.UTF_8)));
                        cmd.add(Base64.getEncoder().encodeToString(rawLinks.getBytes(StandardCharsets.UTF_8)));
                        cmd.add(Base64.getEncoder().encodeToString(chosenPlatform.getBytes(StandardCharsets.UTF_8)));
                        return DesktopBridgeClient.invoke(new ProcessBuilder(cmd), 15_000);
                    }
                    @Override protected void done() {
                        if (!dialog.isDisplayable()) return;
                        review.setEnabled(true);
                        try {
                            Map<String,String> checked = get();
                            if (!chosenPlatform.equals(marketplace.getSelectedIndex() == 0 ? "jd" : "taobao")) {
                                outcome.setText("商城选择已变更，请重新校验所选平台的链接");
                                return;
                            }
                            if (checked.containsKey("error")) throw new IllegalArgumentException(checked.get("error"));
                            String[] urls = checked.getOrDefault("candidate_urls", "").split("\\n");
                            for (String url : urls) if (!url.isBlank()) verifiedLinks.addItem(url);
                            openVerified.setEnabled(verifiedLinks.getItemCount() > 0);
                            outcome.setText(checked.getOrDefault("summary", "无候选")
                                    + "\n\n核验记录（未批准购买）：\n"
                                    + checked.getOrDefault("report_json", "{}"));
                            outcome.setCaretPosition(0);
                        } catch (Exception ex) {
                            outcome.setText("商品链接校验失败：" + ex.getMessage());
                        }
                    }
                };
                worker.execute();
            } catch (IllegalArgumentException ex) {
                JOptionPane.showMessageDialog(dialog, ex.getMessage(), "链接格式不正确", JOptionPane.WARNING_MESSAGE);
            }
        });
        openVerified.addActionListener(e -> {
            try {
                String chosen = (String) verifiedLinks.getSelectedItem();
                if (chosen == null) return;
                URI itemUri = URI.create(chosen);
                String host = itemUri.getHost();
                if (!"https".equals(itemUri.getScheme()) ||
                        !Set.of("item.jd.com", "item.taobao.com", "detail.tmall.com").contains(host))
                    throw new IllegalArgumentException("不是已校验的官方商品详情页");
                if (!Desktop.isDesktopSupported() || !Desktop.getDesktop().isSupported(Desktop.Action.BROWSE))
                    throw new IllegalStateException("当前系统不支持浏览器");
                Desktop.getDesktop().browse(itemUri);
            } catch (Exception ex) {
                JOptionPane.showMessageDialog(dialog, "无法打开商品：" + ex.getMessage(), "打开失败", JOptionPane.WARNING_MESSAGE);
            }
        });
        close.addActionListener(e -> dialog.dispose());
        p.add(buttons(open, review, openVerified, close));
        dialog.add(new JScrollPane(p));
        dialog.setSize(880,720);
        dialog.setLocationRelativeTo(frame);
        dialog.setVisible(true);
    }

    private void previewReport() {
        JTextArea editor = area(18);
        editor.setText(lastReport + "\n\n人工评审意见（请自行填写）：\n");
        editor.setCaretPosition(0);
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
                if (hainaMcpReport != null) {
                    cmd.add("--haina-mcp-report");
                    cmd.add(hainaMcpReport.toString());
                }
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
                result.setText("第四步 · 本机判断\n\n状态："+userStatus+"\n\n理由：\n"+data.get("reasons")+"\n\n需要澄清：\n"+data.get("questions")+"\n\n未核实：\n"+data.get("unknowns")+"\n\n可用于决策的证据：\n"+(data.get("evidence").isBlank()?"无已通过用途及范围审核的决策证据；当前来源仅可作研究线索":data.get("evidence"))+"\n\n候选为只读核查对象；购买建议未批准，交易关闭。");result.setCaretPosition(0);show("four");
            } catch(Exception ex) {error("后端错误，可重试："+ex.getMessage());}}
        };
        pendingWorker=worker;
        worker.execute();
    }
    private void error(String msg) {JOptionPane.showMessageDialog(frame,msg,"请检查",JOptionPane.WARNING_MESSAGE);status.setText(msg);}
    public static void main(String[] args) {String python=args.length>0?args[0]:(System.getProperty("os.name").toLowerCase().contains("win")?"python":"python3");SwingUtilities.invokeLater(()->new ShoppingDecisionDesktop(python));}
}
