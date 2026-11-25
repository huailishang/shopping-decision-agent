"""Bounded ModelScope same-evidence comparison. No tools, no secret logging."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import ssl
import sys
import time
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT))
from shopping_decision.evidence_comparison import build_prompt, digest, response_schema, rule_comparison, validate_model_result
from shopping_decision.claim_gate import publish_checked_comparison
from shopping_decision.model_comparison import write_json

PRIVATE = ROOT / "data/private/modelscope"
MODEL = "Qwen/Qwen3.8-Flash-Next"
CASES = {"C01":"original","C08":"dual-hard","C12":"withdrawn"}

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def key_from_local():
    key = os.environ.get("MODELSCOPE_API_KEY","").strip()
    if not key:
        p = PRIVATE / ".env"
        if p.is_file():
            for line in p.read_text(encoding="utf-8").splitlines():
                if line.startswith("MODELSCOPE_API_KEY="):
                    key = line.partition("=")[2].strip()
    return key

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("case", choices=CASES)
    parser.add_argument('--retry-truncation', action='store_true')
    a = parser.parse_args()
    if a.retry_truncation:
        prior = HERE / ('modelscope-'+a.case) / 'meta.json'
        if a.case not in CASES or not prior.is_file() or json.loads(prior.read_text(encoding='utf-8')).get('failure') not in ('provider_not_completed', 'JSONDecodeError'):
            parser.error('one corrective retry only for a recorded incomplete response')
    label = a.case + ('-r1' if a.retry_truncation else '')
    max_tokens = 8192
    key = key_from_local()
    if not key:
        print("blocked_missing_env_key")
        return 2
    out = HERE / ("modelscope-"+label)
    if out.exists() or len(list(HERE.glob("modelscope-C*"))) >= 4:
        print("attempt_already_recorded_or_limit_reached")
        return 2
    bundle = json.loads((HERE / ("input-"+a.case+".json")).read_text(encoding="utf-8"))
    rule = rule_comparison(bundle)
    prompt = build_prompt(bundle) + "\n请优先说明硬条件反证如何影响候选资格；未知不是失败。仅依据输入解释低频成本与下一行动，简洁输出。\nJSON Schema:\n" + json.dumps(response_schema(bundle), ensure_ascii=False)
    out.mkdir()
    write_json(out/"request.json", bundle)
    write_json(out/"rule-result.json", rule)
    write_json(out/"rule-public.json", publish_checked_comparison(bundle, origin="rule"))
    payload = {"model":MODEL,"input":prompt,"max_output_tokens":max_tokens,"stream":False}
    req = urllib.request.Request("https://api-inference.modelscope.cn/v1/responses",
        data=json.dumps(payload,ensure_ascii=False).encode("utf-8"),
        headers={"Authorization":"Bearer "+key,"Content-Type":"application/json","Accept":"application/json","Accept-Encoding":"identity"},method="POST")
    opener = urllib.request.build_opener(NoRedirect(),urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    started = time.monotonic()
    meta = {"case":a.case,"provider":"modelscope","requested_model":MODEL,
            "input_sha256":digest(bundle),"started_at_utc":datetime.now(timezone.utc).isoformat(),
            "live_attempt":True,"tools_requested":False,"status":"rejected","usage":None,
            "max_output_tokens":max_tokens,"corrective_retry":a.retry_truncation}
    try:
        with opener.open(req,timeout=175) as response:
            meta["http_status"] = response.status
            meta["content_type"] = response.headers.get("Content-Type")
            meta["content_length_header"] = response.headers.get("Content-Length")
            meta["transfer_encoding"] = response.headers.get("Transfer-Encoding")
            raw = response.read(4*1024*1024)
            meta["received_bytes"] = len(raw)
            meta["starts_with_json_object"] = raw.lstrip().startswith(b"{")
        raw_path = PRIVATE / ("tradeoff-20261125-response-"+label+".json")
        with raw_path.open("xb") as f:
            f.write(raw)
        meta["response_sha256"] = hashlib.sha256(raw).hexdigest()
        body = json.loads(raw)
        meta["observed_model"] = body.get("model")
        meta["provider_status"] = body.get("status")
        usage = body.get("usage")
        if isinstance(usage,dict):
            meta["usage"] = {k:v for k,v in usage.items() if k in ("input_tokens","output_tokens","total_tokens") and type(v) is int and v >= 0}
        outputs = body.get("output",[])
        if not isinstance(outputs,list) or any(x.get("type") not in ("message","reasoning") for x in outputs if isinstance(x,dict)):
            raise ValueError("unexpected_output_item_or_tool")
        if body.get("status") not in (None,"completed"):
            raise ValueError("provider_not_completed")
        msg = "".join(part.get("text","") for item in outputs if item.get("type")=="message" for part in item.get("content",[]) if part.get("type")=="output_text").strip()
        if re.fullmatch(r"```(?:json)?\s*[\s\S]+?\s*```",msg,re.I):
            msg = re.sub(r"^```(?:json)?\s*|\s*```$","",msg,flags=re.I)
        result = json.loads(msg)
        write_json(out/"response.json",result)
        checked = validate_model_result(bundle,result)
        checked["verified_public_decision"] = publish_checked_comparison(bundle,checked["model_output"],origin="model")
        write_json(out/"validated.json",checked)
        meta["status"] = "accepted"
    except urllib.error.HTTPError as exc:
        meta["http_status"] = exc.code
        meta["failure"] = "http_error"
    except (ValueError, KeyError, TypeError, OSError, AttributeError) as exc:
        # Only stable error labels; never echo provider response or credentials.
        meta["failure"] = str(exc)[:150] if isinstance(exc,ValueError) and not isinstance(exc,json.JSONDecodeError) else type(exc).__name__
    finally:
        meta["elapsed_seconds"] = round(time.monotonic()-started,3)
        meta["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        write_json(out/"meta.json",meta)
        print(json.dumps(meta,ensure_ascii=False))
    return 0 if meta["status"]=="accepted" else 1

if __name__ == "__main__":
    sys.exit(main())
