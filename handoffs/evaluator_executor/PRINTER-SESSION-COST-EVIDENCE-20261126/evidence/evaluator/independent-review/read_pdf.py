"""One bounded public fetch; keep necessary excerpts/images, not full document."""
import urllib.request,json,hashlib,datetime,fitz
from pathlib import Path
p=Path(__file__).parent
record={'operation':'public PDF fetch and in-memory rendering of necessary pages','read_number':5,'url':'https://h10032.www1.hp.com/ctg/Manual/c07148381.pdf','start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(p/'source-read-05.json').write_text(json.dumps(record,indent=2),encoding='utf8')
try:
    with urllib.request.urlopen(record['url'],timeout=35) as response:
        raw=response.read(12*1024*1024+1)
    if len(raw)>12*1024*1024:raise ValueError('document_limit')
    record.update(raw_document_sha256=hashlib.sha256(raw).hexdigest(),raw_document_bytes=len(raw))
    doc=fitz.open(stream=raw,filetype='pdf')
    record['pages']=len(doc)
    for number,clip,name in [(144,fitz.Rect(30,35,570,430),'model-table'),(67,fitz.Rect(30,30,570,370),'maintenance')]:
        page=doc[number];pix=page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),clip=clip)
        target=p/(name+'.png');pix.save(str(target));record[name+'_sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
    record['result']='necessary cropped pages saved; full PDF memory only'
except Exception as e:record.update(result='failed',exception=type(e).__name__,message=str(e))
record['end_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
(p/'source-read-05.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(record,ensure_ascii=False))
