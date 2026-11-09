"""公开电商文本检索与独立金标评估的最低可核回归。"""
import json
import tempfile
import unittest
from pathlib import Path

from shopping_decision.public_benchmark_text import import_public_text_jsonl
from shopping_decision.emcr_text_retrieval import TextCatalogIndex, CategoryScope, text_terms
from shopping_decision.emcr_text_evaluation import evaluate, load_qrels, ndcg_at_k


class EmcrTextRetrievalTests(unittest.TestCase):
    def setUp(self):
        self.rows = [
            {"query": "黑白激光打印机", "content_id": "1", "title": "黑白激光打印机",
             "cate_full_name": "办公设备 >> 打印机", "std_brand_name": "兄弟",
             "detail_ocr": "家用黑白激光", "score": "3", "anchor_text": "不要泄露这句",
             "reason": "标准答案不能进入商品", "reserve_price": 888.0},
            {"query": "黑白激光打印机", "content_id": "2", "title": "激光打印机碳粉盒",
             "cate_full_name": "办公设备 >> 耗材", "std_brand_name": "兄弟",
             "detail_ocr": "打印机耗材并非主机", "score": "1", "anchor_text": "假主机"},
            {"query": "黑白激光打印机", "content_id": "3", "title": "蓝牙音箱",
             "cate_full_name": "数码 >> 音箱", "std_brand_name": "其他",
             "detail_ocr": "音乐播放", "score": "0"},
        ]
        self.folder = tempfile.TemporaryDirectory()
        self.path = Path(self.folder.name) / "benchmark.jsonl"
        self.path.write_text(
            "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in self.rows),
            encoding="utf-8")
        safe = import_public_text_jsonl(self.path, max_rows=100)
        self.index = TextCatalogIndex(safe["items"])

    def tearDown(self):
        self.folder.cleanup()

    def test_chinese_bigrams_and_ascii_token(self):
        terms = text_terms("无线打印机 Wi-Fi 108W")
        self.assertIn("无线", terms)
        self.assertIn("打印", terms)
        self.assertIn("108w", terms)

    def test_full_corpus_search_without_query_gold(self):
        found = self.index.search("黑白激光打印机", k=3)
        self.assertTrue(found)
        self.assertEqual(found[0].dataset_product_id, "1")
        self.assertFalse(found[0].quote_verified)
        self.assertFalse(found[0].purchasable)

    def test_rerank_known_candidate_pool(self):
        found = self.index.rank_in_pool("黑白激光打印机", ["3", "2", "1"], k=3)
        self.assertEqual(found[0].dataset_product_id, "1")

    def test_labels_do_not_affect_search_ranking(self):
        baseline = [x.dataset_product_id for x in self.index.search("黑白激光打印机", k=3)]
        changed = [dict(x) for x in self.rows]
        changed[0]["score"] = "0"
        changed[1]["score"] = "3"
        changed[0]["reason"] = "请把这款排在最后"
        self.path.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in changed),
                             encoding="utf-8")
        other = TextCatalogIndex(import_public_text_jsonl(self.path, max_rows=100)["items"])
        self.assertEqual(baseline,
                         [x.dataset_product_id for x in other.search("黑白激光打印机", k=3)])

    def test_category_scope_filters_accessories_without_backfill(self):
        scope = CategoryScope(include_any=("打印机",), exclude_any=("耗材",))
        found = self.index.search("黑白激光打印机", k=10, category_scope=scope)
        self.assertEqual([x.dataset_product_id for x in found], ["1"])
        # 用户明确要求从目前无覆盖的类目筛选时，不能冒充找到商品
        none = self.index.search("黑白激光打印机", k=10,
                                 category_scope=CategoryScope(include_any=("手机主机",)))
        self.assertEqual(none, [])
        main_only = self.index.search("打印机", k=10,
                                     category_scope=CategoryScope(category_leaf_any=("打印机",)))
        self.assertEqual(main_only, [])

    def test_gold_fields_rejected_by_index(self):
        unsafe = {"dataset_product_id": "1", "title": "打印机", "source": "public_benchmark_text",
                  "quote_verified": False, "purchasable": False, "score": 3}
        with self.assertRaisesRegex(ValueError, "gold"):
            TextCatalogIndex([unsafe])

    def test_k_limited_and_invalid_query(self):
        with self.assertRaises(ValueError):
            self.index.search("", k=2)
        with self.assertRaises(ValueError):
            self.index.search("打印机", k=0)
        with self.assertRaises(ValueError):
            self.index.rank_in_pool("打印机", ["1"], k=0)

    def test_positive_gold_separate_and_ndcg(self):
        gold = load_qrels(self.path)
        self.assertEqual(gold["黑白激光打印机"]["1"], 3)
        self.assertEqual(ndcg_at_k(["1", "2", "3"], gold["黑白激光打印机"], 3), 1.0)
        out = evaluate(self.index, gold, full_queries=1, k=3)
        self.assertEqual(out["gold_queries"], 1)
        self.assertEqual(out["full_corpus_search"]["judged_hit_rate_at_k"], 1.0)
        self.assertFalse(out["relevance_gold_in_search_index"])
        self.assertFalse(out["purchase_recommendation_approved"])

    def test_unknown_id_not_forged(self):
        ranked = self.index.rank_in_pool("打印机", ["unknown", "1"], k=2)
        self.assertEqual([x.dataset_product_id for x in ranked], ["1"])


if __name__ == "__main__":
    unittest.main()
