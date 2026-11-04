"""H08 本机只读交互服务：python3 -m shopping_decision.web"""
from __future__ import annotations
from dataclasses import asdict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
import re
from pathlib import Path

from .contracts import PurchaseRequest
from .decision import decide
from .knowledge import CARDS_PATH, load_cards
from .route_claims import ROUTE_LEDGER_PATH, load_route_claim_cards
from .product_compare import compare_printer_request, catalogue_sha256

ROOT = Path(__file__).resolve().parent
MAX_BODY = 20_000
FIELDS = ('budget_max_cny', 'needs_color', 'accepts_outsourced_color', 'idle_weeks', 'requires_wireless', 'requires_scan')


def parse_print_volume(data: dict) -> dict:
    """仅解析明确的月印量字段，不声称理解自由需求描述。"""
    raw = data.get('monthly_pages')
    interval = data.get('monthly_pages_range')
    if raw is not None and interval is not None:
        raise ValueError('月印量精确值与区间不能同时填写')
    if interval is not None:
        if (not isinstance(interval, list) or len(interval) != 2
                or any(type(v) is not int or not 0 <= v <= 1000000 for v in interval)
                or interval[0] > interval[1]):
            raise ValueError('月印量范围须为两个非负整数，且下界不能大于上界')
        return {'monthly_pages': None, 'monthly_pages_range': tuple(interval)}
    if raw is None:
        return {'monthly_pages': None, 'monthly_pages_range': None}
    if type(raw) is int and 0 <= raw <= 1000000:
        return {'monthly_pages': raw, 'monthly_pages_range': None}
    if isinstance(raw, str):
        raw = raw.strip()
        match = re.fullmatch(r'([0-9]+)\s*[-–~至]\s*([0-9]+)', raw)
        if match:
            lo, hi = map(int, match.groups())
            if 0 <= lo <= hi <= 1000000:
                return {'monthly_pages': None, 'monthly_pages_range': (lo, hi)}
    raise ValueError('每月张数请填非负整数或闭区间，如50或0–50')


def build_request(data: dict) -> PurchaseRequest:
    if not isinstance(data, dict) or not isinstance(data.get('description'), str) or not data['description'].strip():
        raise ValueError('请填写一句话需求')
    if len(data['description']) > 3000:
        raise ValueError('需求文字请控制在3000字以内')
    if data.get('confirmed') is not True:
        raise ValueError('请先确认整理后的需求')
    if data.get('category', 'printer') != 'printer':
        raise ValueError('当前只支持打印机')
    values = parse_print_volume(data)
    for name in FIELDS:
        v = data.get(name)
        if v is None:
            values[name] = None
        elif name in ('budget_max_cny', 'monthly_pages', 'idle_weeks'):
            if type(v) is not int or v < 0 or v > 1000000:
                raise ValueError(name + ' 必须是合理的非负整数或未知')
            values[name] = v
        elif type(v) is bool:
            values[name] = v
        else:
            raise ValueError(name + ' 只能选是、否或未知')
    reqs = data.get('requirements', [])
    if not isinstance(reqs, list) or len(reqs) > 20 or any(not isinstance(v, str) or len(v) > 300 for v in reqs):
        raise ValueError('其他要求格式不正确')
    # 文本不会被自动解析。必须明确纳入待核对要求，以免忽略用户原始硬条件。
    reqs = [data['description'].strip(), *(r.strip() for r in reqs if r.strip())]
    return PurchaseRequest(category='printer', requirements=tuple(reqs), **values)


def evaluate_input(data: dict) -> dict:
    req = build_request(data)
    record = decide(req)
    cards = {c.id: c for c in load_cards() + load_route_claim_cards()}
    evidence = [{'id': c.id, 'source': c.source_name, 'url': c.url,
                 'published_on': c.published_on, 'captured_on': c.captured_on,
                 'scope': c.scope, 'claim': c.claim, 'exceptions': c.exceptions,
                 'counter_evidence': c.counter_evidence,
                 'approval_record': c.approval_evidence_ref}
                for key in record.recommendation.evidence_ids if (c := cards.get(key))]
    normalized = {'monthly_print_volume': (list(req.monthly_pages_range) if req.monthly_pages_range is not None
                 else ([req.monthly_pages, req.monthly_pages] if req.monthly_pages is not None else None)),
                 'volume_type': ('range' if req.monthly_pages_range is not None else
                                 'exact' if req.monthly_pages is not None else 'unknown'),
                 'home_color_required': req.needs_color,
                 'outsource_color_acceptable': req.accepts_outsourced_color,
                 'budget_max_cny': req.budget_max_cny,
                 'wireless_required': req.requires_wireless,
                 'scan_required': req.requires_scan,
                 'original_text_and_extra_requirements': list(req.requirements)}
    # 商品事实比较独立于技术路线主张的决策批准：只列可核对候选，不修改defer或生成购买推荐。
    if record.recommendation.status in ('clarify', 'invalid', 'unsupported'):
        product_comparison = {'status': 'blocked_until_request_valid', 'candidates': []}
    else:
        product_comparison = compare_printer_request(req)
    return {'request': asdict(req), 'normalized_constraints': normalized,
             'product_comparison': product_comparison,
             'product_catalog_sha256': catalogue_sha256(),
            'recommendation': asdict(record.recommendation),
            'evidence': evidence, 'rejected_evidence': record.rejected_evidence,
            'rejected_inputs': record.rejected_inputs,
            'evaluated_at': datetime.now(timezone.utc).isoformat(),
            'engine': 'shopping_decision.decision.decide',
            'card_sha256': hashlib.sha256(CARDS_PATH.read_bytes()).hexdigest(),
            'research_ledger_sha256': (hashlib.sha256(ROUTE_LEDGER_PATH.read_bytes()).hexdigest()
                                     if ROUTE_LEDGER_PATH.is_file() else None),
            'real_time_prices': False, 'transactions_enabled': False}


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path not in ('/', '/app.js', '/style.css'):
            return self._send(404, b'not found', 'text/plain')
        name = {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css'}[self.path]
        mime = 'text/html; charset=utf-8' if name.endswith('.html') else ('text/javascript; charset=utf-8' if name.endswith('.js') else 'text/css; charset=utf-8')
        return self._send(200, (ROOT / 'static' / name).read_bytes(), mime)

    def do_POST(self):
        if self.path != '/api/decide':
            return self._send(404, b'not found', 'text/plain')
        try:
            length = int(self.headers.get('Content-Length', '-1'))
            if length < 1 or length > MAX_BODY:
                raise ValueError('请求过大或为空')
            data = json.loads(self.rfile.read(length))
            result = evaluate_input(data)
            return self._send(200, json.dumps(result, ensure_ascii=False).encode('utf-8'), 'application/json; charset=utf-8')
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return self._send(400, json.dumps({'error': str(exc)}, ensure_ascii=False).encode('utf-8'), 'application/json; charset=utf-8')
        except Exception:
            return self._send(500, json.dumps({'error': '本机决策服务出错，请重试'}, ensure_ascii=False).encode('utf-8'), 'application/json; charset=utf-8')


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    with ThreadingHTTPServer(('127.0.0.1', args.port), Handler) as server:
        print(f'本机打开 http://127.0.0.1:{args.port}/ （Ctrl+C停止）', flush=True)
        server.serve_forever()


if __name__ == '__main__':
    main()
