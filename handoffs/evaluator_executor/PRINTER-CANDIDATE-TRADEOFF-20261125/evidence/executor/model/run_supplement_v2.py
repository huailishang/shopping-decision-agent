"""Owner-authorized supplementary comparison; no changes to frozen evidence."""
import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import urllib.error
import ssl
import re
import run_compare as c

HERE=Path(__file__).resolve().parent
MODELS={"qwen":"Qwen/Qwen3.5-27B","glm":"ZhipuAI/GLM-4.7-Flash","deepseek":"deepseek-ai/DeepSeek-V4.1-Flash"}
def stamp():
    return datetime.now(timezone.utc).isoformat()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("label",choices=MODELS)
    a=p.parse_args()
    root=HERE/"supplement-20261125"
    root.mkdir(exist_ok=True)
    out=root/a.label
    if out.exists() or len([d for d in root.iterdir() if d.is_dir()])>=3:
        print("already_attempted_or_limit"); return 2
    # Never automatically retry uncertain prior dispatches.
    for f in root.glob("*/meta.json"):
        terminal=f.with_name("terminal.json")
        m=json.loads((terminal if terminal.exists() else f).read_text(encoding="utf-8"))
        if m.get("http_status") in (401,402,403,429) or m.get("quota_or_billing") or m.get("status")=="dispatch_pending":
            print("stop_account_limit_or_uncertain_prior"); return 2
    key=c.key_from_local()
    if not key:
        print("missing_config"); return 2
    frozen=json.loads((HERE/"input-C08.json").read_text(encoding="utf-8"))
    bundle=dict(frozen)
    dims={"scan","color_print","wechat_miniprogram"}
    bundle["request_id"]=frozen["request_id"]+"-supplement-3dims"
    bundle["requirements"]=[r for r in frozen["requirements"] if r["dimension"] in dims]
    bundle["facts"]=[f for f in frozen["facts"] if f["dimension"] in dims]
    sids={f["source_id"] for f in bundle["facts"]}
    bundle["sources"]=[s for s in frozen["sources"] if s["id"] in sids]
    rule=c.rule_comparison(bundle)
    prompt=c.build_prompt(bundle)+"\n只输出JSON。每个解释尽量少于30字；不重复推理过程；如无可靠额外取舍可令tradeoffs为空。\nJSON Schema:\n"+json.dumps(c.response_schema(bundle),ensure_ascii=False,separators=(",",":"))
    payload={"model":MODELS[a.label],"input":prompt,"max_output_tokens":4096,"stream":False}
    req=urllib.request.Request("https://api-inference.modelscope.cn/v1/responses",data=json.dumps(payload,ensure_ascii=False).encode("utf-8"),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json","Accept":"application/json","Accept-Encoding":"identity"},method="POST")
    out.mkdir()
    c.write_json(out/"request.json",bundle)
    c.write_json(out/"rule-result.json",rule)
    c.write_json(out/"rule-public.json",c.publish_checked_comparison(bundle,origin="rule"))
    c.write_json(out/"request-payload.json",payload)
    meta={"model":MODELS[a.label],"source_case":"C08-three-dimensions","input_sha256":c.digest(bundle),"prompt_sha256":hashlib.sha256(prompt.encode()).hexdigest(),"started_at_utc":stamp(),"status":"dispatch_pending","live_attempt":True,"max_output_tokens":4096,"tools_requested":False}
    c.write_json(out/"meta.json",meta)
    start=time.monotonic()
    phase="transport"
    try:
        opener=urllib.request.build_opener(c.NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context()))
        with opener.open(req,timeout=80) as response:
            meta["http_status"]=response.status
            meta["content_type"]=response.headers.get("Content-Type")
            meta["transfer_encoding"]=response.headers.get("Transfer-Encoding")
            meta["quota_headers"]={k:v for k,v in response.headers.items() if ("ratelimit" in k.lower() or "quota" in k.lower()) and len(v)<100}
            raw=response.read(2*1024*1024)
        phase="provider_json"
        meta["received_bytes"]=len(raw)
        rawpath=c.PRIVATE/("tradeoff-supplement-20261125-"+a.label+".json")
        with rawpath.open("xb") as f: f.write(raw)
        meta["response_sha256"]=hashlib.sha256(raw).hexdigest()
        body=json.loads(raw)
        meta["observed_model"]=body.get("model")
        meta["provider_status"]=body.get("status")
        if isinstance(body.get("usage"),dict):
            meta["usage"]={k:v for k,v in body["usage"].items() if k in ("input_tokens","output_tokens","total_tokens") and type(v) is int}
        detail=body.get("incomplete_details")
        if isinstance(detail,dict): meta["incomplete_reason"]=detail.get("reason")
        if body.get("success") is False:
            meta["provider_code"]=body.get("code")
            message=str(body.get("msg","")).lower()
            meta["quota_or_billing"]=any(x in message for x in ("quota","rate limit","balance","billing","额度","余额","限流","限额","次数"))
            raise ValueError("provider_application_error")
        if body.get("error"):
            err=body["error"]
            if isinstance(err,dict):
                code=str(err.get("code",""))
                meta["quota_or_billing"]=any(x in code.lower() for x in ("quota","billing","insufficient","rate_limit","balance"))
            raise ValueError("provider_error")
        if body.get("status") not in (None,"completed"):
            raise ValueError("provider_not_completed")
        if body.get("model")!=MODELS[a.label]:
            raise ValueError("model_identity_mismatch")
        phase="output_json"
        outputs=body.get("output",[])
        if not isinstance(outputs,list) or any(not isinstance(i,dict) or i.get("type") not in ("message","reasoning") for i in outputs):
            raise ValueError("unexpected_output_items")
        meta["output_types"]=[i.get("type") for i in outputs]
        msg="".join(part.get("text","") for item in outputs if item.get("type")=="message" for part in item.get("content",[]) if part.get("type")=="output_text").strip()
        if re.fullmatch(r"```(?:json)?\s*[\s\S]+?\s*```",msg,re.I): msg=re.sub(r"^```(?:json)?\s*|\s*```$","",msg,flags=re.I)
        result=json.loads(msg)
        c.write_json(out/"response.json",result)
        phase="validator"
        checked=c.validate_model_result(bundle,result)
        public=c.publish_checked_comparison(bundle,checked["model_output"],origin="model")
        checked["verified_public_decision"]=public
        c.write_json(out/"validated.json",checked)
        meta["status"]="accepted_structure"
    except urllib.error.HTTPError as e:
        meta["http_status"]=e.code
        meta["status"]="rejected"
        meta["failure"]="http_error"
        if e.code in (401,402,403,429): meta["quota_or_billing"]=True
    except Exception as e:
        meta["status"]="rejected"
        meta["failure"]=type(e).__name__
        if isinstance(e,ValueError) and not isinstance(e,json.JSONDecodeError) and re.fullmatch(r"[a-zA-Z0-9_:-]+",str(e)):
            meta["failure"]=str(e)
        meta["phase"]=phase
    finally:
        meta["elapsed_seconds"]=round(time.monotonic()-start,3)
        meta["finished_at_utc"]=stamp()
        c.write_json(out/"terminal.json",meta)
        print(json.dumps(meta,ensure_ascii=False))
    return 0 if meta["status"]=="accepted_structure" else 1

if __name__=="__main__":
    sys.exit(main())
