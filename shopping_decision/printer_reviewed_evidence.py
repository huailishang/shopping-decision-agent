"""Explicitly enabled, pinned local manufacturer evidence for the two-model pilot."""
from copy import deepcopy
from datetime import date, datetime
from hashlib import sha256
import json
import os
from pathlib import Path

from .evidence_comparison import digest, validate_bundle

PACK_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "printer_reviewed_evidence_v1.json"
# The retained V1 bundle has only a receipt summary, so its approval is withdrawn.
PACK_SHA256 = None
MODELS = ("Brother HL-L1238W", "HP M232dw")
# Only explicit mainland device regions; never a delivery or quote inference.
MAINLAND = frozenset(("中国大陆", "中国大陆河南省", "河南省", "河南"))

def local_bundle(values, version, requirements, today):
    if (PACK_SHA256 is None
            or os.environ.get("SHOPPING_PRINTER_REVIEWED_EVIDENCE") != "1"
            or values.get("category") != "printer"
            or values.get("wechat_required") is not True
            or values.get("accepts_initial_setup") is False
            or values.get("device_deployment_region") not in MAINLAND
            or not requirements):
        return None
    try:
        raw = PACK_PATH.read_bytes()
        if sha256(raw).hexdigest() != PACK_SHA256:
            return None
        pack = json.loads(raw)
        if pack["schema_version"] != 1:
            return None
        source = deepcopy(pack["sources"][0])
        fact = deepcopy(pack["facts"][0])
        captured = date.fromisoformat(source["captured_on"])
        expiry = date.fromisoformat(source["valid_until"])
        observed = datetime.fromisoformat(source["observed_at"])
        if (observed.utcoffset() is None or observed.date() != captured
                or not captured <= today <= expiry
                or source.get("revoked") or fact.get("revoked")
                or source["scope_region"] != "中国大陆"
                or fact["scope_region"] != "中国大陆"):
            return None
        region = values["device_deployment_region"]
        source["scope_region"] = fact["scope_region"] = region
        bundle = {
            "schema_version": 1, "request_id": "reviewed-printer-pilot",
            "category": "printer", "dialogue_version": version,
            "confirmed_values_sha256": digest(values), "as_of": today.isoformat(),
            "region": region, "candidates": [{"id": model} for model in MODELS],
            "requirements": deepcopy(requirements), "sources": [source], "facts": [fact],
        }
        return validate_bundle(bundle)
    except (OSError, ValueError, KeyError, IndexError, TypeError, AttributeError, OverflowError):
        return None

def document_note(bundle):
    source = bundle["sources"][0]
    return ("厂家文档（非实机验证）：Brother HL-L1238W 的兄弟畅享印小程序路径可保留核验；"
            "首次须安装并设置 Brother Mobile Connect、连接打印机并启用联机功能。"
            "后续重绑、账号/网络变化及稳定复用待核；独立转存厂商App路径未证明。"
            "HP M232dw 微信小程序及转App路径均待核。"
            "两款实际应付价未知，不推荐购买。"
            "\n来源：" + source["url"] + "；" + source["locator"]
            + "；资料观察时间：" + source["observed_at"])
