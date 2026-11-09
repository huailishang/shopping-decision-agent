# Shopping Decision Agent｜认知驱动购物智能体

> **先懂品类，再选商品；先有证据，再给推荐；先核验订单，再由用户授权交易。**

项目定位：面向商品、服务及可预订产品的**购买决策智能体**。目前只建设「需求理解 → 品类认知 → 评测证据 → 候选商品 → 比较推荐 → 交易草稿 → 安全交接」能力；暂不自动消费真实资金。**知识不是按品类全部预建：通用决策方法长期复用，每次只按缺口查必要专业资料**（详见[按需品类认知与跨品类复用](docs/06_按需品类认知与跨品类复用.md)）。

## 目标与边界

- **认知层**：将专业评测、技术原理、用户反馈整理成带来源、时效、适用条件的品类规则；先定技术路线，后选型号。
- **导购层**：复用「球球 Shopping Agent」的需求澄清、商品检索、评论 RAG、商品对比和多轮交互思路；与百度优选的品类知识、品牌排行及商品数据接口做可插拔对接。
- **评测层**：吸收 ShopSimulator（中文多轮搜索/比较/交互）及 EComAgentBench（分散隐藏意图/澄清/多指标）的任务与评测思想，统一为我们的独立测评契约。
- **交易层**：京东/淘宝只通过授权的官方 API、获许可的第三方服务或用户主动授权的 UI 操作进行搜索/草稿；创建订单、提交支付等高风险操作需单独授权。与兄弟项目 agentic-payment-trust-lab 对接，但不在本仓复制支付协议和状态机。

> **下一轮渠道范围（2026-11-07）**：京东联盟、淘宝、小红书；已从本轮任务移除拼多多。京东联盟/淘宝用于合规商品发现，小红书用于合法取得的体验与反证。参见 [渠道设计文档](docs/08_商品发现与评价证据渠道_京东淘宝小红书.md)、[评估者执行包](handoffs/P0_2_京东淘宝小红书_商品发现与评价证据_评估者执行包_20261107.md)；均未宣称已接通平台业务接口，原 P0.2 执行成果不变。

> **P0.5 双平台发现接入（2026-11-07）**：已实现京东联盟旧JOS关键词查询的签名构造与官方返回结构解析、淘宝客官方物料返回解析、跨平台候选去重与型号线索回查。官方淘宝物料 `num_iid` 已标废弃，优先 `item_id` 并拦截冲突。**实际两平台业务授权请求0、有效实时地区报价0**；合成源回放京东1商品（2来源）+淘宝1商品（1来源），不代表真实商品发现。Python **231/231**、旧负向 **8/8**、Java原有回归 **4/4、6/6** 均通过。见 [P0.5详细执行报告](reports/P0_5_双平台官方商品发现_执行报告_20261107.md) 与 [CURRENT.md](CURRENT.md)。

> **P0.4 新增商品发现入口（2026-11-07）**：Java Swing 第一屏及结果页新增「京东商城商品发现（只读实验）」按钮。用户输入任意品类搜索词，**本人点击**打开本机默认浏览器的京东搜索页，可自行登录并复制1～5条商品详情 URL 回填；程序离线校验网址/商品编号、去重并保留审计记录。**不是自动京东 API 搜索或真实核价**：商品型号、地区报价、库存、卖家和购买资格都保持待核，原打印机决策结果不变。见 [P0.4 执行报告](reports/P0_4_Java商城发现入口_20261107.md) 与 [CURRENT.md](CURRENT.md)。Windows 继续使用 `desktop/start_windows.bat`；已验证 WSL JDK17 编译、Java↔Python 联调、Python181/181及旧负向8/8，Windows GUI 点击验收待办；未登录账号、未下单。

> **此前执行状态（2026-11-06）**：正常入口为 Java Swing（`desktop/start_windows.bat`）。已接通5款官网型号事实比较，P0.2补充微信方式、自动双面、预算口径/地区确认，以及京东主机与耗材公开页回查记录。渠道当前返回受限页/登录跳转，**有效实时报价为0，5款预算均未知、购买未批准、交易关闭**；127/127单测及8/8旧负向通过，执行者已作Windows界面自查，独立验收待办。真实知识卡仍未获决策批准，测试通过不等于推荐有效。任务入口见 [CURRENT.md](CURRENT.md) 和 [P0.2执行报告](reports/P0_2_只读零售核验_执行报告_20261106.md)。

## 项目主链

```text
自然语言购买需求
  → 场景要素（预算/频率/性能/偏好/禁忌）
  → 品类知识（稳定规律 + 反例 + 适用范围 + 来源）
  → 用户澄清（缺失的关键条件）
  → 路线选择（例如黑白激光 vs 墨仓）
  → 商品候选（有来源的 SKU / 价格 / 耗材 / 评论）
  → 对比与解释（支持/反对证据、总拥有成本）
  → 推荐结论 / 暂缓决策
  → 订单草稿与显式确认（真实交易默认关闭）
  → 可信支付实验台（独立项目、独立授权）
```

## 第一验证场：家用打印机

- 需求：每月 0–50 页，黑白为主，偶尔彩印，长期闲置可能性高，预算 1000 元，重视耗材成本/可靠性。
- 预期：先说明技术路线与适用条件，再筛机型；不能把「长期闲置=一定买某品牌」当成无条件事实。
- 要测：能否准确提炼评测意见、区分产品参数与营销话术、识别相互矛盾的用户评价；是否能说明为什么不选某款。
- 禁止：编造 SKU、库存、促销价、评价、来源；没有价格来源时不得给出所谓实时到手价。

## 目录

```text
AGENTS.md                     开发与安全规则
CURRENT.md                    唯一当前进度/后续入口
CONTEXT.md                    业务术语
docs/01_核心能力与架构.md      领域流程和模块契约
docs/02_开源复用与授权.md      四个项目的对照与接入边界
docs/03_评测设计.md            指标、样本、基准映射、验收标准
docs/04_平台交易边界.md        京东/淘宝、登录会话、可信支付边界
docs/06_按需品类认知与跨品类复用.md  通用按需研究/来源时效/新类目迁移
knowledge/source_directory.json 可信来源角色索引（不是开放的测评数据库）
handoffs/                     当前角色任务与交接
shopping_decision/             无外部依赖的合成基线（非真实智能体）
examples/                     合成案例
tests/                        本地回归
```

## 本地验证

在项目根目录使用 Python 3.11+（WSL/Linux 用 `python3`；Windows 可改用 `python`）：

```bash
python3 -m unittest discover -s tests -v
python3 -m shopping_decision.demo
python3 -m shopping_decision.h05_probes  # 新负向输入8例，仅离线；不覆盖历史报告
```

P0.2公开渠道回查须显式运行 `python -m shopping_decision.retail`：只请求已登记的京东主机/耗材页，保存访问摘要至 `knowledge/printer_retail_checks.json`，原始HTML留在忽略目录 `data/raw/`。正常桌面读取该摘要，不自动访问平台；当前适配器只能记录可访问性和缺字段，不能输出有效实时报价。页面受限时不登录、不绕过限制，预算继续未知。

当前代码是一个**透明、可复验的规则基线和契约原型**，不调用大模型，不提供真实商品链接或真实下单功能。后续将接入正式的知识检索、LLM 策略、商品平台适配和双基准映射，逐步与该基线比较。

## 核心引用

- 百度优选开放平台：https://openai.baidu.com/ （能力服务，需要权限/凭证）
- 球球 Shopping Agent：https://github.com/pingfangww/qiuqiu-rag-shopping-agent （实现参考，许可需审查）
- ShopSimulator：https://github.com/ShopAgent-Team/ShopSimulator （中文购物环境与评测，许可需审查）
- EComAgentBench：https://github.com/Morizeyao/EComAgentBench_ （隐藏意图评测，许可及数据需审查）

本项目不包含上述项目的源码、模型权重、数据集或任何用户账号凭证，新增代码独立编写。

H03 增加 `shopping_decision/research_router.py`（通用品类证据规划器）、`knowledge/source_directory.json`（来源职责索引）与 `tests/test_research_router.py`。目前能给陌生品类列出按需研究/复核清单，**不能替代真实联网取证，也不代表已经支持跨品类商品推荐**。

## H08：本机打印机交互原型（2026-11-01）

在项目根目录启动（只监听本机）：

```bash
python3 -m shopping_decision.web
# Windows 可使用 python -m shopping_decision.web
```

打开 `http://127.0.0.1:8765/`，在启动的终端按 `Ctrl+C` 停止。填写一句话需求，再由本人补全并确认印量、预算、彩印、外包、闲置和其他硬条件；修改后重新调用本地后端判断。刷新页面会清空本次输入，不默认写文件或上传。评审JSON仅通过“预览评审记录”显示，保存前应人工隐去个人信息。无模型解析、实时商品报价或支付能力。**真实浏览器点击验收/真实用户独立评审仍待完成**；服务端 HTTP 检验及65项单测已通过。详情见 [H08执行报告](reports/H08_执行报告.md)。


## H08最终交互方向：Java Swing 桌面窗口

**以Java桌面窗口为主，不需要浏览器。** 安装JDK 17+及Python 3.11+，在Windows资源管理器双击 `desktop/start_windows.bat` 即可编译并打开窗口（也可以在项目根目录命令行执行）。窗口包含一句话需求、条件补充、人工确认、后端判断、修改重算和评审记录预览。Java仅为UI层，每次判断以Python子进程运行已有 `decide()`；无新增第三方Java依赖、无需HTTP服务或浏览器。Windows须保证 `javac`、`java`、`python` 在PATH中。若找不到Python，请检查解释器命令。原有Web单页仅作为先前工程试验保留，不再作为首选入口。

**验收边界：** Java 17编译、Java→Python文本协议和68项单测已经通过；图形化窗口的人工鼠标点击/截图尚未完成，真人需求与独立推荐效果评审未通过。关闭窗口即结束，不启用真实电商交易。


### H10 桌面版进程输出修复

Swing 通过 `DesktopBridgeClient` 同步消费Python完整审计输出，避免先等子进程退出造成管道阻塞。Windows入口仍为 `desktop/start_windows.bat`；通过 `python -m unittest discover -s tests -q` 及 `python -m shopping_decision.h05_probes` 复验。Java进程专项可用 `javac -encoding UTF-8 -d .h08-build desktop/DesktopBridgeClient.java desktop/H10JavaRegression.java`、`java -cp .h08-build H10JavaRegression python`（Linux上使用python3）。修复后的Windows GUI完整点击仍需独立验收，详见 `reports/H10_执行修复报告.md`。


## P0 首批真实商品候选事实与比较（2026-11-04）

这不是完整电商导购：已实现厂商官网**型号发现→来源事实快照→硬条件三态对比→Java桌面结果展示**。原路线主张审批不变；`defer`依然代表尚无通过独立评估的路线推荐，`product_comparison`是只读的型号事实比较，不表示已获购买批准。

在项目目录执行：

```bash
# 1. 只读发现 Brother 中国目录现有的黑白激光型号（无账号、无购物）
python3 -m shopping_decision.official_model_discovery --out reports/p0_brother_discovery_local.json

# 2. 回查已登记的官方产品来源；只检型号字符串和来源哈希，不自动改写产品字段
python3 -m shopping_decision.official_source_check --model HL-L1238W

# 3. 商品对比走原正常输入/桌面桥接；测试可复验所有控制边界
python3 -m unittest discover -s tests -q
python3 -m shopping_decision.h05_probes
```

首批产品事实在 `knowledge/printer_products_official.json`（兄弟3款+HP2款；型号、源URL、功能证据、耗材和厂商建议零售价），通用比较器为 `shopping_decision/product_compare.py`；没有联网的实时京东/淘宝到手价、库存或平台SKU。现有Java桌面启动方式不变。**官网建议零售价不是实际到手价**；如果无法核验当前购买价格，所有预算判定必须显示未知。Brother公开目录已经能发现额外型号，但发现记录并不自动成为经过确认的商品功能。查看 [P0执行报告](reports/P0_真实商品候选与比较_执行报告_20261104.md) 和 [CURRENT.md](CURRENT.md)。
