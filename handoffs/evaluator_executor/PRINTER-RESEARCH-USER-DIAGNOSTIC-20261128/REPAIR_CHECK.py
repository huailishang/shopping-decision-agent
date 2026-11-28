from PREP_BASELINE import HERE,OUT,inventory,git,now
import hashlib,json,sys,time,subprocess
P=OUT/'repair-20261128'
def save(name,d):
    with (P/name).open('x',encoding='utf8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
def snapshot():
    return dict(files=inventory(),head=git('rev-parse','HEAD').decode().strip(),index=hashlib.sha256(git('ls-files','--stage','-z')).hexdigest())
def main(mode):
    P.mkdir(exist_ok=True)
    t=time.monotonic();start=now()
    if mode=='before':
        save('before.json',snapshot());print('BASELINE')
    elif mode=='after':
        b=json.loads((P/'before.json').read_text(encoding='utf8'));a=snapshot()
        changed=sorted(k for k in set(a['files'])|set(b['files']) if a['files'].get(k)!=b['files'].get(k))
        save('scope.json',dict(count=len(a['files']),changed=changed,head_same=a['head']==b['head'],index_same=a['index']==b['index'],started=start,ended=now(),elapsed=time.monotonic()-t))
        assert not changed and a['head']==b['head'] and a['index']==b['index'];print('SCOPE',len(a['files']))
    else:raise ValueError(mode)
if __name__=='__main__':main(sys.argv[1])
