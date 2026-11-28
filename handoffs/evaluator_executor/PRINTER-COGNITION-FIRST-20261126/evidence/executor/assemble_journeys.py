"""Assemble the measured paths from raw native events and actual subprocess returns."""
from pathlib import Path
import json,hashlib
E=Path(__file__).resolve().parent;ROOT=E.parents[4]
N=E/'java-native-20261127T074238427479'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
expected={r['id']:r for r in read(E/'expectations.json')['cases']}
native=read(N/'summary.json');assert native['passed']
log=(N/'CognitionGuideSwingRegression.stdout.txt').read_text(encoding='utf8')
bridge={r['id']:r for r in read(E/'remaining-journey-results.json')}
pairs=read(E/'comparisons.json')['pairs']
actions=read(E/'action-slice03-final.json')
details={
 'G01':('仅粗用途，未确认专业参数','真实窗口先出现指南，来源与生活化问题可读','G01-guide.txt'),
 'G02':('彩印选择尚未明确','彩色必须排黑白，外包可考虑；不把原两款当唯一范围','G02-color.txt G02-outsourced.txt'),
 'G03':('只知道粗用途','指南显示参数解释、反证、原地址、发布/获取日期及定位','G03-source-details.txt'),
 'G04':('已有会话','点击参考仅填草稿，会话原字节不变','G04-draft.txt'),
 'G05':('未确认闲置因素','发送后often_long进入状态，恢复/维护问题出现','G05-confirmed.txt'),
 'G06':('已确认闲置因素','暂缓、改答、撤回按实际按钮流程保真','G06-withdrawn.txt'),
 'G13':('方法来源有效；用户已确认场景','受控撤回与同ID新版待审，旧主张失效，独立主张及答案保持；恢复原注册表后重算','G13-before.txt G13-withdrawn.txt G13-revision2.txt G13-recovered.txt'),
 'G14':('当前指南、已确认闲置因素','另存、新会话、新进程恢复；只保留输入及引用、不恢复结论','G14-saved.json G14-restored.txt'),
 'G15':('当前产品报告','实际预览/选择文件并另存，来源/版本/授权false可读','G15-decision-note.json'),
 'G16':('有效会话与已存在文件','取消、错误枚举、拒绝覆盖、实际新会话使旧worker失效；旧草稿取消另有原生证据','G16-note-cancel.txt G16-reset-and-fault.txt J09-after.txt'),
}
description={
 'G07':('原已准入资料','合成广告/自证注入拒绝，待审摘录不升级认知或事实'),
 'G08':('原已准入资料','合成转载/冲突旧价及不适用型号均待审，不改变事实；美国方法限制保留'),
 'G09':('硬条件待核','彩色硬要求两旧款不适用；成本假设不能复活硬失败'),
 'G10':('未做成本情景','决定说明分层保留本人需求、认知、型号事实、标称量和假设；价格未核'),
 'G11':('正常真实stdin指南及规则结果','真实产品上下文由受控transport消费；伪造/陈旧回执和超预算回退，不调用真实模型'),
 'G17':('已完成合成同口径工作单','0与未知区分，拒绝极端费用/单候选币种错误，正常修改恢复'),
 'G18':('专家直接确认所需参数','不强制指南阅读，已有条件保留且不重复追问确认字段'),
 'G20':('当前已有资料','受控清空来源注册表后无supported主张，仍保留本人答案和具体补证；恢复原资料后重算'),
}
cases=[]
for i in range(1,21):
 ident=f'G{i:02d}';exp=expected[ident]
 if ident in details:
    before,after,names=details[ident]
    ok='PASS '+ident in log
    refs=[ref(N/n) for n in names.split()]+[ref(N/'CognitionGuideSwingRegression.stdout.txt'),ref(N/'summary.json')]
    if ident=='G13':refs+=[ref(E/'five-suites-05.stdout.txt')]
    if ident=='G16':refs+=[ref(N/'DecisionWorksheetSwingRegression.stdout.txt')]
    route='java_event'
 elif ident in bridge:
    r=bridge[ident];ok=r['passed'];before,after=description[ident]
    refs=[r['raw_artifact'],ref(E/'run_remaining_journeys.py')];route='bridge_process'
 elif ident=='G12':
    ok=actions['passed']==actions['total']==3
    before='原前测仅1/3，行动固定追随赢家随箱量'
    after='冻结探针维护/主机价/随箱量3/3定位实际干预对象；两点情景，不是全范围证明'
    refs=[ref(E/'action-slice03-final.json')];route='bridge_process'
 elif ident=='G19':
    ok=len(pairs)==6 and all(not p[arm]['output']['metrics']['safety_error'] for p in pairs for arm in ('a','b'))
    before='固定同资料、同偏好oracle、同资源上限的配对参考'
    after='六对实际后端双臂最终决策指标持平；明确无真实用户收益证明'
    refs=[ref(E/'comparisons.json'),ref(E/'paired-reference-v1.json'),ref(E/'B1-shared-product-snapshot.json')]+[q for p in pairs for arm in ('a','b') for q in p[arm]['raw_artifacts']];route='bridge_process'
 else:raise AssertionError(ident)
 cases.append(dict(id=ident,core=exp['core'],completed=bool(ok),route=route,expected=exp['expected'],before=before,after=after,raw_artifacts=refs,
    safety_violations=[] if ok else ['未完成，不能确认无错误']))
write(E/'journeys.json',dict(schema_version=1,cases=cases))
print('assembled',len(cases),sum(x['completed'] for x in cases))
