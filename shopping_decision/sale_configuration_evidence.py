"""P0.9-B：销售配置证据的受限离线校验；不等于平台实时核验或购买批准。

只允许显式 synthetic_test 的合同测试。本机无法凭一个JSON自称的平台截图/许可
证明真实权威来源，真实数据分支须先由独立的权限及原件审核流程启用。
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
import re

from .model_identifiers import extract_model_tokens as find_models, is_model_token

REAL_SALE_EVIDENCE_ENABLED = False
_PLATFORMS = frozenset({"JD", "TAOBAO"})
_ALLOWED_ROW_KEYS = frozenset((
    "source_id", "platform", "platform_item_id", "selected_sku_id",
    "seller_id", "selected_variant", "selected_model_id", "title_models",
    "spec_models", "item_kind", "condition", "source_ref", "source_sha256",
    "observed_at", "review_valid_until", "review_status",
    "field_anchors", "permitted_uses",
))
_ID = re.compile(r"[0-9]{5,20}")
_SAFE = re.compile(r"[A-Za-z0-9_:-]{1,100}")
_SHA = re.compile(r"[0-9a-f]{64}")
_REQUIRED_ANCHORS = frozenset(("platform_item_id", "seller_id", "selected_variant",
                                "selected_model_id", "item_kind", "condition"))
_REQUIRED_USES = frozenset(("local_parse", "user_display", "minimal_audit"))


def _instant(value: object, current: datetime) -> datetime | None:
    if not isinstance(value, str) or len(value) > 50:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.year < 2020:
            return None
        # 本地偏移在UTC换算时可能越过datetime的可表示年份。
        normalized = parsed.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return None
    if normalized > current:
        return None
    return normalized


def _source_safe(value: object, *, prefix: str = "") -> bool:
    return (isinstance(value, str) and 1 <= len(value) <= 100
            and (not prefix or value.startswith(prefix))
            and bool(_SAFE.fullmatch(value)))


def _validate(row: dict, now: datetime, known_models: set[str]) -> tuple[dict | None, str]:
    # 不能接受输入自己提供的已核、报价、交易、地区可售等“批准结果”。
    if not isinstance(row, dict) or not set(row).issubset(_ALLOWED_ROW_KEYS):
        return None, "unrecognized_or_forbidden_fields"
    platform, item_id, sku_id = row.get("platform"), row.get("platform_item_id"), row.get("selected_sku_id")
    if (not isinstance(platform, str) or platform not in _PLATFORMS
            or not isinstance(item_id, str) or not _ID.fullmatch(item_id)):
        return None, "platform_or_item_id_invalid"
    if sku_id is not None and (not isinstance(sku_id, str) or not _ID.fullmatch(sku_id)):
        return None, "sku_id_invalid"
    if not (_source_safe(row.get("source_id"), prefix="synthetic:")
            and _source_safe(row.get("source_ref"), prefix="synthetic:")
            and _source_safe(row.get("seller_id"))):
        return None, "source_or_seller_invalid"
    if (not isinstance(row.get("source_sha256"), str)
            or not _SHA.fullmatch(row["source_sha256"])):
        return None, "source_hash_invalid"
    if (row.get("item_kind") != "printer" or row.get("condition") != "new"
            or row.get("selected_variant") != "single_new_printer"):
        return None, "not_single_new_printer"
    if row.get("review_status") != "active":
        return None, "review_withdrawn_or_unconfirmed"
    selected = row.get("selected_model_id")
    tokens = find_models(selected)
    approved = {value.upper() for value in known_models if isinstance(value, str)}
    if not is_model_token(selected) or len(tokens) != 1 or tokens[0] not in approved:
        return None, "manufacturer_model_not_reviewed"
    model = selected
    selected = tokens[0]
    for field in ("title_models", "spec_models"):
        values = row.get(field)
        token_values = find_models(values[0]) if isinstance(values, list) and len(values) == 1 else []
        if (not isinstance(values, list) or len(values) != 1
                or not isinstance(values[0], str) or len(token_values) != 1
                or token_values[0] != selected):
            return None, "title_spec_or_selected_model_conflict"
    anchors = row.get("field_anchors")
    if (not isinstance(anchors, dict)
            or not _REQUIRED_ANCHORS.issubset(anchors)
            or not set(anchors).issubset(_REQUIRED_ANCHORS | {"selected_sku_id"})
            or any(not _source_safe(value, prefix="synthetic:") for value in anchors.values())):
        return None, "platform_field_anchor_missing"
    # 向后兼容旧synthetic夹具：缺SKU锚点仍可做有限合同测试，
    # 但必须标记为证据不完整，不能称已完成所选SKU字段绑定。
    sku_anchored = "selected_sku_id" in anchors
    uses = row.get("permitted_uses")
    if (not isinstance(uses, list) or len(uses) != len(_REQUIRED_USES)
            or any(not isinstance(use, str) for use in uses)
            or set(uses) != _REQUIRED_USES):
        return None, "required_local_uses_not_evidenced"
    observed = _instant(row.get("observed_at"), now)
    if observed is None:
        return None, "source_observation_invalid"
    valid_until = _instant(row.get("review_valid_until"), now)
    # 有效期可以是未来时刻，但必须由记录给出且不早于当前时刻。
    if valid_until is None:
        try:
            raw_expiry = row.get("review_valid_until")
            if not isinstance(raw_expiry, str) or len(raw_expiry) > 50:
                return None, "review_expiry_invalid"
            valid_until = datetime.fromisoformat(raw_expiry.replace("Z", "+00:00"))
            if valid_until.tzinfo is None or valid_until.year < 2020:
                return None, "review_expiry_invalid"
            valid_until = valid_until.astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError):
            return None, "review_expiry_invalid"
    if valid_until < now or valid_until < observed:
        return None, "review_expired"
    # 未标SKU时，不能用商品级ID冒充具体选中配置（本包合成测试宁可保守拒绝）。
    if sku_id is None:
        return None, "selected_sku_id_missing"
    return {
        "platform": platform, "platform_item_id": item_id, "selected_sku_id": sku_id,
        "seller_id": row["seller_id"], "selected_model_id": model,
        "observed_at": observed.isoformat(), "review_valid_until": valid_until.isoformat(),
        "source_id": row["source_id"], "source_sha256": row["source_sha256"],
        "source_ref": row["source_ref"], "field_anchors": dict(anchors),
        "sku_anchor_status": ("synthetic_selected_sku_anchor_recorded"
                              if sku_anchored else "missing_selected_sku_anchor_unverified"),
        "field_binding_complete": sku_anchored,
        "status": "synthetic_field_binding_test_only",
        "identity_verified": False, "quote_verified": False, "purchasable": False,
        "budget_status": "unknown_no_authorized_regional_quote",
    }, "accepted_synthetic"


def _stable_source_event(row: object, current: datetime) -> tuple | None:
    """只给本轮同源冲突判定使用的键，不把自述撤回当可信外部事件。"""
    if not isinstance(row, dict):
        return None
    platform = row.get("platform")
    item = row.get("platform_item_id")
    sku = row.get("selected_sku_id")
    seller = row.get("seller_id")
    source = row.get("source_id")
    source_ref = row.get("source_ref")
    sha = row.get("source_sha256")
    observed = _instant(row.get("observed_at"), current)
    if (not isinstance(platform, str) or platform not in _PLATFORMS
            or not isinstance(item, str) or not _ID.fullmatch(item)
            or not isinstance(sku, str) or not _ID.fullmatch(sku)
            or not _source_safe(seller) or not _source_safe(source, prefix="synthetic:")
            or not _source_safe(source_ref, prefix="synthetic:")
            or not isinstance(sha, str) or not _SHA.fullmatch(sha)
            or observed is None):
        return None
    return (platform, item, sku, seller, source, source_ref, sha, observed.isoformat())


def _validated_state_event(row: object, current: datetime,
                           known_models: set[str]) -> tuple | None:
    """状态变更是特殊合成事件；拒绝的坏行不能拥有撤回正常行的副作用。"""
    if not isinstance(row, dict) or not set(row).issubset(_ALLOWED_ROW_KEYS):
        return None
    status = row.get("review_status")
    uses = row.get("permitted_uses")
    if status not in ("active", "withdrawn"):
        return None
    # 只有严格减少原已核的用途或明确withdrawn才是状态事件；
    # 禁止字段、未知用途、嵌套类型与重复用途均不能产生撤回效力。
    if (not isinstance(uses, list) or len(uses) > len(_REQUIRED_USES)
            or any(not isinstance(use, str) or use not in _REQUIRED_USES for use in uses)
            or len(set(uses)) != len(uses)):
        return None
    if status != "withdrawn" and set(uses) == _REQUIRED_USES:
        return None

    # 仅为复用活动证据的全字段校验，临时复原事件前状态；
    # 除review_status/合法用途减少之外，任何其它不合格字段都不能放行事件。
    baseline = {**row, "review_status": "active",
                "permitted_uses": sorted(_REQUIRED_USES)}
    validated, _ = _validate(baseline, current, known_models)
    if validated is None:
        return None
    return _stable_source_event(validated, current)


def assess_sale_evidence_report(report: dict, *, now: datetime | None = None,
                                known_models: set[str] | None = None) -> dict:
    """逐行校验、跨平台/SKU隔离、同键冲突不吞；结果绝不能升级真实身份。"""
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("naive_clock")
    if known_models is None:
        from .p0_7_official_details import load_reviewed_local_replay
        try:
            catalog = load_reviewed_local_replay()
            known_models = {x["model_id"] for x in catalog["products"]
                            if x.get("manufacturer_detail_evidence") is not None}
        except (ValueError, OSError):
            known_models = set()
    if not isinstance(report, dict) or set(report) != {"operation", "source_mode", "items"}:
        raise ValueError("invalid_sale_evidence_envelope")
    if report["operation"] != "p0_9_b_sale_configuration_evidence":
        raise ValueError("invalid_sale_evidence_operation")
    if report["source_mode"] != "synthetic_test" or REAL_SALE_EVIDENCE_ENABLED:
        # 生产模式不是可由输入文件自主声明的能力；真实授权尚未开放。
        raise ValueError("real_sale_evidence_import_not_authorized")
    rows = report["items"]
    if not isinstance(rows, list) or len(rows) > 20:
        raise ValueError("invalid_sale_evidence_rows")
    accepted, rejected = [], []
    invalidated_events = set()
    for index, row in enumerate(rows, 1):
        result, reason = _validate(row, current, known_models)
        if result is None:
            rejected.append({"row": index, "reason": reason})
            # 普通校验拒绝后的行默认只有拒绝计数；状态事件要再次按
            # 完整结构校验，不能凭被拒行自述的withdrawn/用途字段作废好行。
            event = _validated_state_event(row, current, known_models)
            if event is not None:
                invalidated_events.add(event)
        else:
            accepted.append(result)
    groups = defaultdict(list)
    for entry in accepted:
        groups[(entry["platform"], entry["platform_item_id"],
                entry["selected_sku_id"], entry["seller_id"])].append(entry)
    output = []
    for entries in groups.values():
        # 同键其他独立来源仍可保留，不因一个来源撤回就连坐。
        blocked = [x for x in entries if _stable_source_event(x, current) in invalidated_events]
        for x in blocked:
            output.append({**x, "status": "synthetic_same_source_invalidated_requires_review"})
        entries = [x for x in entries if _stable_source_event(x, current) not in invalidated_events]
        if not entries:
            continue
        models = {x["selected_model_id"] for x in entries}
        hashes = {x["source_sha256"] for x in entries}
        observation_events = {(x["source_sha256"], x["observed_at"],
                               x["review_valid_until"]) for x in entries}
        if len(models) > 1 or len(hashes) > 1 or len(observation_events) > 1:
            for x in entries:
                output.append({**x, "status": "synthetic_source_conflict_requires_review"})
        else:
            # 同键多来源不转成更多票数或现行报价。
            output.append({**entries[0], "source_count": len(entries)})
    return {
        "operation": "p0_9_b_sale_configuration_evidence_gate",
        "source_mode": "synthetic_test", "status": "synthetic_only_no_real_identity",
        "input_rows": len(rows), "accepted_rows": len(accepted),
        "rejected_count": len(rejected), "rejected": rejected,
        "configuration_count": len(output), "configurations": output,
        "real_identity_verified_count": 0, "verified_quote_count": 0,
        "purchase_recommendation_approved": False, "transactions_enabled": False,
        "limitations": [
            "合成证据只能验证绑定规则，不能代表平台原件、用户授权或真实配置",
            "商品级ID与所选SKU不可互代；同商品不同SKU、不同平台分开",
            "平台字段、供应商字段和厂商规格各自需要来源；本报告没有地区现价",
        ],
    }
