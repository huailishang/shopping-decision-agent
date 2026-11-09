"""纯文本购物目录搜索实验：完全不依赖金标、历史价、商品图片或商城账号。

输入只读取 public_benchmark_text 的商品安全字段；不能读取 eMCR 的查询、
anchor/score/reason 等评测字段作为索引信息。返回只是静态候选，不是购买推荐。
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import heapq
import math
from pathlib import Path
import re
import unicodedata

from .public_benchmark_text import import_public_text_jsonl


_WORD_RE = re.compile(r"[\u3400-\u9fff]+|[a-z0-9]+")
_ALLOWED_FIELDS = ("title", "category_hint", "brand_hint", "properties_text", "description")


def text_terms(text: str) -> Counter[str]:
    """确定性 CJK 双字词 + 拉丁/数字分词；不下载中文分词模型。"""
    normalized = unicodedata.normalize("NFKC", text).casefold()
    result: Counter[str] = Counter()
    for m in _WORD_RE.finditer(normalized):
        run = m.group(0)
        if "\u3400" <= run[0] <= "\u9fff":
            if len(run) == 1:
                result[run] += 1
            else:
                result.update(run[i:i + 2] for i in range(len(run) - 1))
        else:
            result[run] += 1
    return result


@dataclass(frozen=True)
class TextHit:
    dataset_product_id: str
    title: str
    category_hint: str | None
    score: float
    source: str = "public_benchmark_text"
    purchasable: bool = False
    quote_verified: bool = False


@dataclass(frozen=True)
class CategoryScope:
    """用户/上游明确给出的商品类别范围；未指定时不能假装模型已做品类辨别。"""
    include_any: tuple[str, ...] = ()
    exclude_any: tuple[str, ...] = ()
    category_leaf_any: tuple[str, ...] = ()

    def allows(self, category_hint: str | None) -> bool:
        cat = category_hint or ""
        leaf = cat.split(">>")[-1].strip()
        if self.category_leaf_any and leaf not in self.category_leaf_any:
            return False
        if self.include_any and not any(x in cat for x in self.include_any):
            return False
        return not any(x in cat for x in self.exclude_any)


class TextCatalogIndex:
    """目录只接收被过滤的商品文本；评测标签必须在调用者的另一份结构中。"""

    def __init__(self, safe_items: list[dict]):
        if not isinstance(safe_items, list) or not safe_items:
            raise ValueError("empty_corpus")
        self.items = []
        self.ids: dict[str, int] = {}
        self.weights: list[Counter[str]] = []
        self.lengths: list[float] = []
        self.postings: dict[str, list[tuple[int, float]]] = defaultdict(list)
        for item in safe_items:
            if (not isinstance(item, dict) or item.get("source") != "public_benchmark_text"
                    or item.get("quote_verified") is not False
                    or item.get("purchasable") is not False
                    or not isinstance(item.get("dataset_product_id"), str)
                    or not isinstance(item.get("title"), str)):
                raise ValueError("unsafe_catalog_item")
            if any(k in item for k in ("query", "anchor_id", "anchor_text", "score",
                                       "reason", "reserve_price", "live_price_cny",
                                       "doc_image", "anchor_image")):
                raise ValueError("benchmark_gold_or_price_leak")
            pid = item["dataset_product_id"]
            if pid in self.ids:
                raise ValueError("duplicate_corpus_id")
            doc_num = len(self.items)
            self.ids[pid] = doc_num
            self.items.append({k: item.get(k) for k in ("dataset_product_id", "title", "category_hint")})
            terms = Counter()
            for field, weight, char_limit in (
                ("title", 4, 500), ("category_hint", 2, 200),
                ("brand_hint", 3, 100), ("properties_text", 1, 500),
                ("description", 1, 260),
            ):
                raw = item.get(field)
                if isinstance(raw, str):
                    for term, count in text_terms(raw[:char_limit]).items():
                        terms[term] += count * weight
            self.weights.append(terms)
            length = float(sum(terms.values()))
            self.lengths.append(length)
            for term, count in terms.items():
                self.postings[term].append((doc_num, float(count)))
        self.n = len(self.items)
        self.avg_length = sum(self.lengths) / self.n
        self.doc_freq = {term: len(post) for term, post in self.postings.items()}

    def _query_terms(self, query: str) -> list[tuple[str, float]]:
        if not isinstance(query, str) or not query.strip() or len(query) > 500:
            raise ValueError("invalid_query")
        seen = text_terms(query)
        return [
            (term, math.log1p((self.n - self.doc_freq[term] + 0.5) /
                              (self.doc_freq[term] + 0.5)))
            for term in seen
            if term in self.doc_freq and self.doc_freq[term] / self.n <= 0.6
        ]

    def _part_score(self, doc_num: int, count: float, idf: float) -> float:
        denominator = count + 1.2 * (0.25 + 0.75 * self.lengths[doc_num] / self.avg_length)
        return idf * count * 2.2 / denominator

    def rank_in_pool(self, query: str, product_ids: list[str], *, k: int = 10) -> list[TextHit]:
        """只在给定候选中排序；这是限定候选排序，不是全库召回。"""
        if not 1 <= k <= 100 or not isinstance(product_ids, list) or len(product_ids) > 1000:
            raise ValueError("invalid_pool")
        terms = self._query_terms(query)
        scores = []
        for pid in dict.fromkeys(product_ids):
            idx = self.ids.get(pid)
            if idx is None:
                continue
            s = sum(self._part_score(idx, self.weights[idx].get(t, 0), idf)
                    for t, idf in terms if self.weights[idx].get(t, 0) > 0)
            scores.append((s, pid))
        scores.sort(key=lambda pair: (-pair[0], pair[1]))
        return [self._hit(pid, score) for score, pid in scores[:k]]

    def search(self, query: str, *, k: int = 10,
               category_scope: CategoryScope | None = None) -> list[TextHit]:
        """在全部商品中搜索，可指定显式品类范围；不使用 gold 候选名单。"""
        if type(k) is not int or not 1 <= k <= 100:
            raise ValueError("invalid_limit")
        scores: dict[int, float] = defaultdict(float)
        for term, idf in self._query_terms(query):
            for doc_num, tf in self.postings[term]:
                scores[doc_num] += self._part_score(doc_num, tf, idf)
        if category_scope is not None:
            if not isinstance(category_scope, CategoryScope):
                raise ValueError("invalid_category_scope")
            scores = {i: score for i, score in scores.items()
                      if category_scope.allows(self.items[i]["category_hint"])}
        best = heapq.nlargest(k, scores.items(), key=lambda it: (it[1], -it[0]))
        return [self._hit(self.items[i]["dataset_product_id"], score)
                for i, score in best]

    def _hit(self, pid: str, score: float) -> TextHit:
        doc = self.items[self.ids[pid]]
        return TextHit(dataset_product_id=pid, title=doc["title"],
                       category_hint=doc["category_hint"], score=round(score, 5))


def load_text_index(jsonl_file: Path) -> TextCatalogIndex:
    result = import_public_text_jsonl(jsonl_file, max_rows=50000)
    if result["status"] != "text_candidates_unverified" or result["schema_unmapped"]:
        raise ValueError("unmapped_source_schema")
    return TextCatalogIndex(result["items"])


def main() -> None:
    """本地中文搜索CLI，显式要求范围；不输出金标、历史报价或购买建议。"""
    import argparse
    import json
    from dataclasses import asdict
    parser = argparse.ArgumentParser(description="eMCR离线商品文本搜索（非实时商城）")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("query", type=str)
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--include-category", action="append", default=[])
    parser.add_argument("--exclude-category", action="append", default=[])
    parser.add_argument("--category-leaf", action="append", default=[],
                        help="严格匹配类目最后一级，不把打印机配件冒充打印机主机")
    args = parser.parse_args()
    idx = load_text_index(args.dataset)
    scope = CategoryScope(include_any=tuple(args.include_category),
                          exclude_any=tuple(args.exclude_category),
                          category_leaf_any=tuple(args.category_leaf))
    hits = idx.search(args.query, k=args.top, category_scope=scope)
    print(json.dumps({
        "query": args.query, "source": "eMCR_fixed_retrieval_benchmark",
        "corpus_size": idx.n, "category_scope": asdict(scope),
        "search_hits": [asdict(hit) for hit in hits],
        "status": "unverified_text_candidates" if hits else "no_category_qualified_candidates",
        "current_price_approved": False, "purchasable": False,
        "transactions_enabled": False,
        "limitations": ["这是历史评测语料，类目仅为商品文本，非在售主机识别或实时价格",
                        "相关性分数不等于满足用户条件，所有商品需复核具体型号和配置"]
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
