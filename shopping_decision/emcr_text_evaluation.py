"""eMCR 固定文本基准评估；gold 与独立商品索引分离。

候选池排序基准（每题约30条）与全库搜索分开汇报。
未标注全库商品的相关性未知，不能将搜索结果当真实商品价格或质量结论。
"""
from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
from pathlib import Path
import argparse
import json
import math

from .emcr_text_retrieval import load_text_index, TextCatalogIndex

KNOWN_SCORES = {0, 1, 2, 3}


def load_qrels(path: Path) -> dict[str, dict[str, int]]:
    if not path.is_file() or path.stat().st_size > 180_000_000:
        raise ValueError("missing_gold_file")
    gold = defaultdict(dict)
    with path.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError("invalid_gold_row")
            query, pid, label = row.get("query"), row.get("content_id"), row.get("score")
            if (not isinstance(query, str) or not query
                    or not isinstance(pid, str) or not pid
                    or not isinstance(label, str) or not label.isdigit()
                    or int(label) not in KNOWN_SCORES):
                raise ValueError("invalid_gold_label")
            score = int(label)
            if pid in gold[query] and gold[query][pid] != score:
                raise ValueError("conflicting_gold")
            gold[query][pid] = score
    return dict(gold)


def ndcg_at_k(ranked_ids: list[str], gold: dict[str, int], k: int) -> float:
    def gain(label: int, index: int) -> float:
        return (2 ** label - 1) / math.log2(index + 2)
    observed = sum(gain(gold.get(pid, 0), i) for i, pid in enumerate(ranked_ids[:k]))
    ideal = sum(gain(score, i) for i, score in
                enumerate(sorted(gold.values(), reverse=True)[:k]))
    return observed / ideal if ideal > 0 else 0.0


def _mean(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def evaluate(index: TextCatalogIndex, gold: dict[str, dict[str, int]],
             *, full_queries: int = 120, k: int = 10) -> dict:
    if type(full_queries) is not int or not 1 <= full_queries <= 1399:
        raise ValueError("invalid_full_query_limit")
    if type(k) is not int or not 1 <= k <= 30:
        raise ValueError("invalid_k")
    if not gold:
        raise ValueError("empty_benchmark")
    candidate_ndcg, candidate_hit, positive_covered, no_positive = [], [], 0, 0
    for query, judgments in gold.items():
        candidate_ids = list(judgments)
        if len(candidate_ids) > 1000:
            raise ValueError("oversized_judgment_pool")
        # 只给 rank_in_pool 商品ID，不提供 label/score/reason 或 anchor。
        ranked = [hit.dataset_product_id for hit in
                  index.rank_in_pool(query, candidate_ids, k=k)]
        if any(score >= 2 for score in judgments.values()):
            positive_covered += 1
            candidate_hit.append(float(any(judgments.get(pid, 0) >= 2 for pid in ranked)))
            candidate_ndcg.append(ndcg_at_k(ranked, judgments, k))
        else:
            no_positive += 1
    # hash选择冻结查询子集，选择不依赖金标值与检索结果。
    fixed_queries = sorted(gold, key=lambda x: sha256(x.encode("utf-8")).hexdigest())[:full_queries]
    full_ndcg, full_hit, judged_recall = [], [], []
    inspected = []
    for query in fixed_queries:
        labels = gold[query]
        if not any(v >= 2 for v in labels.values()):
            continue
        ranked = [hit.dataset_product_id for hit in index.search(query, k=k)]
        positive = sum(v >= 2 for v in labels.values())
        matched = sum(labels.get(pid, 0) >= 2 for pid in ranked)
        full_ndcg.append(ndcg_at_k(ranked, labels, k))
        full_hit.append(float(matched > 0))
        judged_recall.append(matched / positive)
        if len(inspected) < 8:
            inspected.append({
                "query": query, "top_ids": ranked,
                "judged_positive_found": matched,
                "judged_positive_total": positive,
            })
    return {
        "experiment": "emcr_text_lexical_baseline",
        "retrieval_method": "CJK_bigrams_ASCII_words_BM25_no_model",
        "corpus_products": index.n, "gold_queries": len(gold), "k": k,
        "candidate_pool_rerank": {
            "evaluated_queries_with_judged_positive": positive_covered,
            "queries_without_judged_positive": no_positive,
            "mean_ndcg_at_k": round(_mean(candidate_ndcg), 5),
            "judged_hit_rate_at_k": round(_mean(candidate_hit), 5),
            "candidate_pool_provided": True,
            "cannot_claim_open_corpus_discovery": True,
        },
        "full_corpus_search": {
            "hash_frozen_query_count": len(fixed_queries),
            "evaluated_queries_with_judged_positive": len(full_ndcg),
            "mean_judged_ndcg_at_k": round(_mean(full_ndcg), 5),
            "judged_hit_rate_at_k": round(_mean(full_hit), 5),
            "mean_judged_recall_at_k": round(_mean(judged_recall), 5),
            "unjudged_products_count_as_zero_only_for_proxy_metric": True,
            "samples": inspected,
        },
        "source_kind": "static_public_retrieval_benchmark_not_current_retail",
        "uses_images": False, "relevance_gold_in_search_index": False,
        "verified_current_quotes": 0, "purchase_recommendation_approved": False,
        "transactions_enabled": False,
        "limitations": [
            "候选池排序只证明约30条已给候选的排序能力，非全网商品发现",
            "全库排名里未标注商品按零分计算代理NDCG，可能错判实际相关商品；只能对已标注商品计算命中",
            "文本双字词基线无法保证否定/数量单位/隐性意图的正确理解",
            "图片未下载，不做多模态评测",
            "静态eMCR价格、销量、库存与当前购买结论不具实时资格",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="eMCR 中文商品文本检索双路径基准")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--full-queries", type=int, default=120)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    index = load_text_index(args.dataset)
    gold = load_qrels(args.dataset)
    result = evaluate(index, gold, full_queries=args.full_queries)
    output = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
    print(output, end="")


if __name__ == "__main__":
    main()
