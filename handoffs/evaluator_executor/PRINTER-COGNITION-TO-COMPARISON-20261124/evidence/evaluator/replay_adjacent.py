"""Independent neighboring business probes and offline model receipt audit."""
from copy import deepcopy
from datetime import date
from hashlib import sha256
import json
import re
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))
from shopping_decision import cognition_comparison as cog
from shopping_decision.chat_bridge import new_dialogue, render_chat, submit_message
from shopping_decision.evidence_comparison import digest, validate_model_result
from shopping_decision.claim_gate import publish_checked_comparison


def main():
    state = new_dialogue()
    for field, value in (
        ("category", "打印机"), ("usage", "家用低频打印"),
        ("needs_color", "是"), ("accepts_outsourced_color", "否"),
        ("monthly_pages_range", "0-50"), ("budget_max_cny", "1000"),
        ("device_deployment_region", "中国大陆河南省"),
        ("wechat_required", "偏好"), ("requires_scan", "是"),
    ):
        state = submit_message(state, field, value)
    pack = cog.load_pack()
    negative = deepcopy(pack["facts"][0])
    negative.update(id="synthetic-color-negative", dimension="color_print", value=False,
                    statement="合成负向测试：候选为黑白输出",
                    kind="synthetic_probe", source_id="synthetic-color-source")
    source = deepcopy(pack["sources"][0])
    source.update(id="synthetic-color-source", url="https://probe.invalid/color")
    pack["sources"].append(source)
    pack["facts"].append(negative)
    with patch.object(cog, "load_pack", return_value=pack):
        view = render_chat(state)
    audit = json.loads(view["report_json"])
    row = next(c for c in audit["cognition_comparison"]["public"]["claims"]
               if c["candidate_id"] == "HP M232dw" and c["dimension"] == "color_print")
    hard_case = {"basis": "synthetic intervention only", "text": view["result_text"],
                 "color_claim_status": row["status"],
                 "still_prioritizes_scan_candidate": "HP M232dw在该维度有依据，可优先核查" in view["result_text"],
                 "flags": {key: audit[key] for key in (
                     "purchase_recommendation_approved", "transactions_enabled", "live_price_verified")}}
    model_root = HERE.parent / "executor" / "model"
    model_checks = []
    for name in ("modelscope-C01", "modelscope-C04-r1", "modelscope-C08"):
        folder = model_root / name
        request = json.loads((folder / "request.json").read_bytes())
        response_raw = (folder / "response.json").read_bytes()
        response = json.loads(response_raw)
        meta = json.loads((folder / "meta.json").read_bytes())
        label = name.removeprefix("modelscope-")
        raw_http = (ROOT / "data/private/modelscope" / ("response-" + label + ".json")).read_bytes()
        body = json.loads(raw_http)
        message = "".join(part.get("text", "") for item in body.get("output", [])
                          if item.get("type") == "message"
                          for part in item.get("content", []) if part.get("type") == "output_text").strip()
        if message.startswith("```"):
            message = re.sub(r"^```(?:json)?\s*|\s*```$", "", message, flags=re.I)
        validated = validate_model_result(request, response)
        public = publish_checked_comparison(request, response, origin="model")
        rule = json.loads((folder / "rule-public.json").read_bytes())
        model_checks.append({
            "case": name, "request_hash_matches": digest(request) == meta["input_sha256"],
            "raw_http_hash_matches": sha256(raw_http).hexdigest() == meta["response_sha256"],
            "extracted_response_matches_raw": json.loads(message) == response,
            "validation_accepted": bool(validated),
            "claims_equal_rule": public["claims"] == rule["claims"],
            "reported_http_status": meta["http_status"],
            "reported_usage": meta["usage"],
        })
    result = {"hard_condition_probe": hard_case, "offline_model_revalidation": model_checks}
    (HERE / "adjacent-results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
