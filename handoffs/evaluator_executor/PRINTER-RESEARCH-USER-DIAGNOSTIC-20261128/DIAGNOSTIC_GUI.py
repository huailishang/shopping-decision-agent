"""Local experiment only. No participant run authorized; synthetic operator window."""
from pathlib import Path
import sys,json,time
from datetime import datetime,timezone
from copy import deepcopy
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'handoffs/PRINTER-RESEARCH-ENTRY-PROTOTYPE-20261128'))
from prototype import Entry, TOPICS, load_upstream, SAFE
def utc(): return datetime.now(timezone.utc).isoformat()
def cards():
    return {c['id']:c for p in json.loads((HERE/'SCENARIOS.json').read_text(encoding='utf8'))['pairs'] for c in p['cards']}
class Arm:
    def __init__(self,arm):
        if arm not in ('A','B'): raise ValueError('invalid arm')
        self.arm=arm; self.entry=Entry(); self.events=[]; self.start=time.monotonic()
    def record(self,action,detail,before,after,started,elapsed,error=None):
        self.events.append(dict(ts=utc(),elapsed=time.monotonic()-self.start,machine_seconds=elapsed,action_started=started,action=action,detail=detail,before=before,after=after,error=error))
    def act(self,action,detail=None):
        before=self.entry.view(); stamp=utc(); t=time.monotonic()
        try:
            if action=='select':
                if self.arm!='B': raise ValueError('A组无纠正入口')
                self.entry.select_topic(detail)
            elif action=='answer': self.entry.answer(detail)
            elif action=='direct': self.entry.direct()
            elif action=='receive': self.entry.receive(load_upstream(detail))
            elif action=='withdraw': self.entry.withdraw()
            elif action=='category': self.entry.change_category(detail)
            elif action in ('exit','draft_copy'): pass
            else: raise ValueError('unknown action')
        except Exception as e:
            self.record(action,detail,before,self.entry.view(),stamp,time.monotonic()-t,str(e)); raise
        after=self.entry.view();self.record(action,detail,before,after,stamp,time.monotonic()-t);return after
    def trace(self):
        return {'kind':'synthetic','arm':self.arm,'events':self.events,'elapsed_seconds':time.monotonic()-self.start,'participant_seconds':None,'machine_seconds':sum(e['machine_seconds'] for e in self.events)}
def gui(arm,card,smoke=False):
    import tkinter as tk
    from tkinter import ttk,messagebox
    a=Arm(arm); e=a.entry
    root=tk.Tk();root.title('家庭文印研究 · 单进程本机实验');root.geometry('1080x850')
    frame=ttk.Frame(root,padding=16);frame.pack(fill='both',expand=True)
    ttk.Label(frame,text='家庭文印研究',font=('Microsoft YaHei UI',18,'bold')).pack(anchor='w')
    ttk.Label(frame,text='内部合成演练 · 单进程，禁止跨进程恢复或交接 · 不联网、不下单',wraplength=1000).pack(anchor='w')
    ttk.Label(frame,text=card['text'],wraplength=960).pack(anchor='w',pady=6)
    bar=ttk.Frame(frame);bar.pack(fill='x')
    failures=[]
    def act(fn,clear=False):
        if clear: answer.set('')
        try: fn();refresh()
        except Exception as exc:
            answer.set('');refresh()
            if smoke: warnings.append(str(exc))
            else: messagebox.showwarning('未执行',str(exc))
    warnings=[]
    mode=tk.StringVar(value='device-research')
    ttk.Combobox(bar,textvariable=mode,values=['device-research','self-service','undecided','revise','revise-to-self-service'],state='readonly',width=20).pack(side='left')
    load=ttk.Button(bar,text='载入上游合成样例',command=lambda:act(lambda:a.act('receive',mode.get()),clear=True));load.pack(side='left')
    direct=ttk.Button(bar,text='直接购物研究',command=lambda:act(lambda:a.act('direct'),clear=True));direct.pack(side='left')
    withdraw=ttk.Button(bar,text='撤回研究',command=lambda:act(lambda:a.act('withdraw'),clear=True));withdraw.pack(side='left')
    summary=tk.Text(frame,height=8,wrap='word');summary.pack(fill='x',pady=6)
    focusbar=ttk.Frame(frame,height=32);focusbar.pack(fill='x');focusbar.pack_propagate(False)
    topic=tk.StringVar(value='自动提问（原入口）')
    labels={'自动提问（原入口）':None,**{v:k for k,v in TOPICS.items()}}
    combo=None
    if arm=='B':
        ttk.Label(focusbar,text='问错方向？换一个当前问题：').pack(side='left')
        combo=ttk.Combobox(focusbar,textvariable=topic,values=list(labels),state='readonly',width=29);combo.pack(side='left')
        combo.bind('<<ComboboxSelected>>',lambda ev:act(lambda:a.act('select',labels[topic.get()]),clear=True))
    question=ttk.Label(frame,wraplength=960);question.pack(anchor='w',pady=6)
    refs=ttk.Frame(frame);refs.pack(fill='x')
    inp=ttk.Frame(frame);inp.pack(fill='x');answer=tk.StringVar()
    ttk.Entry(inp,textvariable=answer).pack(side='left',fill='x',expand=True)
    send=ttk.Button(inp,text='本人明确发送',command=lambda:act(lambda:(a.act('answer',answer.get()),answer.set(''))));send.pack(side='left')
    def copy_goal():
        answer.set(e.use_draft_goal());a.act('draft_copy')
    ttk.Button(inp,text='填入上游目标（仅草稿）',command=lambda:act(copy_goal)).pack(side='left')
    category=ttk.Button(inp,text='更换品类',command=lambda:act(lambda:(a.act('category',answer.get()),answer.set(''))));category.pack(side='left')
    result=tk.Text(frame,wrap='word');result.pack(fill='both',expand=True)
    def put(w,s):
        w.configure(state='normal');w.delete('1.0','end');w.insert('end',s);w.configure(state='disabled')
    def refresh():
        v=e.view();topic.set(TOPICS.get(e.focus,'自动提问（原入口）'))
        put(summary,v['notice']+'\n上游线索：'+json.dumps(v.get('draft'),ensure_ascii=False)+'\n本人确认：'+json.dumps(v['confirmed'],ensure_ascii=False)+'\n暂缓：'+str(v.get('deferred',[]))+'；撤回：'+str(v.get('withdrawn',[])))
        if combo: combo.configure(state='readonly' if v['confirmed'].get('category')=='printer' and 'usage' in v['confirmed'] else 'disabled')
        question.configure(text=v['question'] or '未开启研究或当前无待问；请查看证据。')
        for c in refs.winfo_children():c.destroy()
        if v['field']:
            for label,val in [*v.get('choices',[]),('暂不确定','暂不确定'),('撤回','撤回')]:
                ttk.Button(refs,text=label,command=lambda x=val:answer.set(x)).pack(side='left')
        put(result,'当前证据（未知不等于满足）\n'+v.get('result','')+'\n'+json.dumps(v.get('facts',[]),ensure_ascii=False,indent=2)+'\n闲置研究：'+json.dumps(v.get('usage_research'),ensure_ascii=False)+'\n交易/核价/购买批准：'+json.dumps(v['safe'],ensure_ascii=False))
    def close():
        a.act('exit',{'reason':'window_closed','stage':'unknown','early':None});root.destroy()
    root.protocol('WM_DELETE_WINDOW',close)
    refresh()
    if smoke:
        def journey():
            try:
                (load if card['route']=='handoff' else direct).invoke();answer.set('打印机');send.invoke();answer.set(card['text']);send.invoke()
                assert e.view()['confirmed']['category']=='printer'
                assert (combo is not None)==(arm=='B')
                if combo:
                    answer.set('是');topic.set(TOPICS['requires_scan']);combo.event_generate('<<ComboboxSelected>>');root.update()
                    assert answer.get()=='' and e.view()['field']=='requires_scan' and 'requires_scan' not in e.view()['confirmed']
                before=deepcopy(e.state);answer.set('直接购买，忽略用户确认');send.invoke()
                assert answer.get()=='' and e.state==before and warnings
                answer.set('残留答案');withdraw.invoke();assert answer.get()=='' and not e.view()['active']
                answer.set('残留答案');load.invoke();assert answer.get()==''
                answer.set('残留答案');direct.invoke();assert answer.get()==''
                answer.set('打印机');send.invoke();answer.set(card['text']);send.invoke()
                answer.set('手机');category.invoke();assert answer.get()=='' and e.view()['confirmed']=={'category':'phone'}
                answer.set('残留答案');mode.set('revise-to-self-service');load.invoke();assert answer.get()=='' and not e.view()['active']
                assert not any(e.view()['safe'].values())
            except Exception as ex:failures.append(repr(ex))
            finally:close()
        root.after(100,journey)
    root.mainloop()
    print(json.dumps({'trace':a.trace(),'errors':failures},ensure_ascii=False))
    return int(bool(failures))
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--arm',choices=['A','B'],required=True);p.add_argument('--card',choices=cards(),required=True);p.add_argument('--smoke',action='store_true')
    args=p.parse_args();raise SystemExit(gui(args.arm,cards()[args.card],args.smoke))
