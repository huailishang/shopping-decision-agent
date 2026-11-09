"""eMCR 等公开商品检索 JSONL 的离线文本入口（受限 schema 探针）。

未读到官方实际数据行时不得宣称 schema 兼容通过。检索器只能读取
ID / 标题 / 描述白名单；query / anchor / score / reason 及 price 都不得
进入商品内容证据，也不能成为用户实时报价或购买建议。
"""
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json

_ALLOWED_ID = ("content_id", "product_id", "item_id", "sku_id", "id")
_ALLOWED_TITLE = ("product_title", "item_title", "title", "name")
_ALLOWED_DESCRIPTION = ("detail_ocr", "product_description", "description", "product_text", "text")
_MAX_FILE = 180_000_000
_MAX_LINE = 180_000
_ALLOWED_CATEGORY = ("cate_full_name", "category")
_ALLOWED_BRAND = ("std_brand_name", "brand")
_ALLOWED_PROPERTIES = ("property_kvs",)


def _first_string(row: dict, keys: tuple[str, ...], cap: int) -> str | None:
    for key in keys:
        v = row.get(key)
        if isinstance(v, str) and v.strip() and len(v) <= cap:
            return v.strip()
        if key in _ALLOWED_ID and type(v) is int and v >= 0:
            return str(v)
    return None


def import_public_text_jsonl(path: Path, *, max_rows: int = 1000) -> dict:
    """安全导入公开搜索基准商品**文本线索**，丢弃题目答案和价格。

    一些基准行的真实结构不同，本函数会按行报告 schema_unmapped，
    而不是擅自把 anchor_text / reason 当成商品正文。
    """
    if type(max_rows) is not int or not 1 <= max_rows <= 50000:
        raise ValueError("invalid_limit")
    if not path.is_file() or not 0 < path.stat().st_size <= _MAX_FILE:
        raise ValueError("dataset_missing_or_oversized")
    report = {"operation": "offline_public_text_benchmark_import",
              "source_kind": "fixed_benchmark_not_live_catalog",
              "source_file": path.name, "source_sha256": None,
              "scanned_rows": 0, "supported_rows": 0, "schema_unmapped": 0,
              "conflicting_duplicate_ids": 0, "items": [],
              "relevance_labels_excluded": True, "historic_price_is_live_quote": False,
              "quote_verified_count": 0, "purchase_recommendation_approved": False,
              "transactions_enabled": False}
    seen = {}
    conflicted = set()
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for raw in f:
            if report["scanned_rows"] >= max_rows:
                break
            if len(raw) > _MAX_LINE:
                raise ValueError("dataset_line_too_large")
            digest.update(raw)
            if not raw.strip():
                continue
            report["scanned_rows"] += 1
            try:
                row = json.loads(raw)
            except (UnicodeDecodeError, ValueError) as exc:
                raise ValueError(f"invalid_jsonl_line:{report['scanned_rows']}") from exc
            if not isinstance(row, dict):
                report["schema_unmapped"] += 1
                continue
            product = row.get("product")
            product = product if isinstance(product, dict) else row
            pid = _first_string(product, _ALLOWED_ID, 120)
            title = _first_string(product, _ALLOWED_TITLE, 500)
            desc = _first_string(product, _ALLOWED_DESCRIPTION, 6000)
            category = _first_string(product, _ALLOWED_CATEGORY, 300)
            brand = _first_string(product, _ALLOWED_BRAND, 120)
            properties = _first_string(product, _ALLOWED_PROPERTIES, 4000)
            if pid is None or title is None:
                report["schema_unmapped"] += 1
                continue
            identity = (pid, title, desc, category, brand, properties)
            if pid in conflicted:
                continue
            if pid in seen:
                if seen[pid] != identity:
                    report["conflicting_duplicate_ids"] += 1
                    conflicted.add(pid)
                    report["items"] = [item for item in report["items"]
                                       if item["dataset_product_id"] != pid]
                    report["supported_rows"] -= 1
                continue
            seen[pid] = identity
            report["supported_rows"] += 1
            report["items"].append({
                "dataset_product_id": pid, "title": title,
                "description": desc, "category_hint": category,
                "brand_hint": brand, "properties_text": properties,
                "source": "public_benchmark_text",
                "identity_verified": False, "quote_verified": False,
                "purchasable": False,
                "missing_fields": ["current_market_listing", "seller", "sku_variant",
                                   "delivery_region", "stock", "authorized_live_quote"],
            })
    report["source_sha256"] = digest.hexdigest()
    report["sha256_scope"] = "processed_rows_only"  # 并不伪称全文件哈希
    report["status"] = (
        "text_candidates_unverified" if report["items"] else "no_supported_product_schema")
    report["limitations"] = [
        "只用于许可允许的固定语料研究，未做实际电商/全市场发现",
        "未读取商品图片，不能声明多模态指标",
        "数据集文件格式支持需通过真实文件单独验收；纯合成单测不算实际接入",
        "搜索相关性得分不等于商品质量、真实价格或购买资格",
    ]
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="公开电商 JSONL 安全文本探针（无网络/无实时报价）")
    parser.add_argument("path", type=Path)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    result = import_public_text_jsonl(args.path, max_rows=args.limit)
    print(json.dumps({k: v for k, v in result.items() if k != "items"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
