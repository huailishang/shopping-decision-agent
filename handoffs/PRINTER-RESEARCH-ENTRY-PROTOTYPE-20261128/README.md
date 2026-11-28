# 本机文印研究入口实验样稿

在购物仓库根目录使用现有 Windows Python（不安装依赖）：

```powershell
& 'D:\SoftWare\Anaconda\install\python.exe' -X utf8 handoffs/PRINTER-RESEARCH-ENTRY-PROTOTYPE-20261128/prototype.py
```

同一命令追加 `--smoke` 自动运行真实Tk窗口操作后关闭。WSL本机复跑：`PYTHONPATH=handoffs/PRINTER-RESEARCH-ENTRY-PROTOTYPE-20261128:.:tests python3 -X utf8 handoffs/PRINTER-RESEARCH-ENTRY-PROTOTYPE-20261128/test_prototype.py`。

先载入合成设备研究草案，明确输入打印机；可点击填入上游目标作为输入草稿，再明确发送。选“换一个当前问题”只改变提问，不写答案。确认扫描后可用同一入口补齐必要条件。选择自助/暂缓应留在非购物；测试改选请使用 revise-to-self-service（上游实际函数生成合成revision 3）。重复送达不恢复已撤回研究。直接购物研究无需上游草案。

仅合成实验，非正式接收API，版本去重仅在当前窗口内存，未认证跨进程/持久化交接。独立实验窗口，不改原Java主屏或现有购物桥；无真实用户、实时价格、订单、模型调用。
