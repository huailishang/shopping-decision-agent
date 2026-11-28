"""Continue the already-frozen H07 cases; only answer actual displayed fields."""
from independent_checks import *

def main():
    rows=[]
    cases=[('把老人手写的旧家谱变成电脑文件','requires_scan','是'),
           ('两面都要印，家人不会自己翻纸','requires_auto_duplex','是'),
           ('暑假结束后收柜子里，到寒假才用','idle_weeks_pattern','经常连续多周不用')]
    for i,(usage,wanted,answer) in enumerate(cases):
        folder=HERE/'holdouts'/('H07-continuation-'+str(i));folder.mkdir(parents=True,exist_ok=False)
        with tempfile.TemporaryDirectory(prefix='eval-h07-') as d:
            base=Path(d);populate(base);s=state(usage);trace=[]
            for turn in range(13):
                v=call(base,folder,str(turn),s)
                field=v['prompt_field'];trace.append(dict(turn=turn,field=field,prompt=v['prompt'],safe=safe(v)))
                if field==wanted or not field:break
                # Same semantic policy as the original reference: unknown stays unknown.
                s=submit_message(s,field,'暂不确定')
            row=dict(usage=usage,wanted=wanted,asked=any(t['field']==wanted for t in trace),trace=trace)
            rows.append(row);print(json.dumps(row,ensure_ascii=False),flush=True)
    save(HERE/'h07-continuation.json',rows)
if __name__=='__main__':main()
