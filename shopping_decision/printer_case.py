"""首个真实需求的人工比较基线。只呈现受限型号事实与条件性取舍，不签发推荐。"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from .contracts import PurchaseRequest, monthly_page_bounds
from .evidence_policy import valid_https_url

BASELINE_PATH = Path(__file__).resolve().parents[1] / 'knowledge' / 'printer_case_baseline.json'
MODELS = frozenset(('HL-L1238W', 'HP-Laser-108w', 'HL-L1228'))
SOURCE_HOSTS = frozenset(('www.brother.cn', 'download.brother.com', 'h30471.www3.hp.com'))
SOURCE_FIELDS = ('id', 'url', 'source_kind', 'captured_on', 'document_date', 'date_note', 'limit', 'content_sha256')


def load_case_baseline(path: Path = BASELINE_PATH, *, today: date | None = None) -> dict:
    today = today or date.today()
    data = json.loads(path.read_text(encoding='utf-8'))
    if (not isinstance(data, dict) or data.get('schema_version') != 1
            or data.get('status') != 'executor_research_comparison_not_approved'):
        raise ValueError('比较基线格式/资格不正确')
    captured = date.fromisoformat(data['recorded_on'])
    if captured > today:
        raise ValueError('比较基线日期不能在未来')
    if not isinstance(data.get('sources'), list) or not isinstance(data.get('models'), list):
        raise ValueError('缺来源或型号记录')
    if not all(isinstance(data.get(k), str) and data[k].strip() for k in ('case_id', 'scope')):
        raise ValueError('比较缺案例或适用范围')
    sources, urls, digests = {}, set(), set()
    for source in data['sources']:
        if not isinstance(source, dict):
            raise ValueError('来源格式不正确')
        if any(k not in source for k in SOURCE_FIELDS):
            raise ValueError('来源元信息不完整')
        sid, url, digest = source.get('id'), source.get('url'), source.get('content_sha256')
        if (not isinstance(sid, str) or not sid or sid in sources
                or not valid_https_url(url) or urlsplit(url).hostname not in SOURCE_HOSTS
                or url in urls or not isinstance(digest, str) or not re.fullmatch(r'[a-f0-9]{64}', digest)
                or digest in digests):
            raise ValueError('来源缺失、重复或不在本轮厂商来源范围')
        if source.get('source_kind') not in ('manufacturer_spec', 'manufacturer_setup'):
            raise ValueError('广告、体验或外部评测不能冒充本轮厂商型号基线')
        if (not isinstance(source.get('models'), list) or not source['models']
                or any(m not in MODELS for m in source['models'])
                or not all(isinstance(source.get(k), str) and source[k].strip() for k in ('date_note', 'limit'))
                or not (source['document_date'] is None or isinstance(source['document_date'], str))):
            raise ValueError('来源缺型号、日期语义或局限')
        if date.fromisoformat(source['captured_on']) > today:
            raise ValueError('来源获取日在未来')
        sources[sid] = source
        urls.add(url); digests.add(digest)
    seen = set()
    for model in data['models']:
        if not isinstance(model, dict):
            raise ValueError('型号记录格式不正确')
        mid = model.get('model_id')
        if mid not in MODELS or mid in seen or not isinstance(model.get('notes'), list) or not model['notes']:
            raise ValueError('型号缺失、重复或不在三型号范围')
        seen.add(mid)
        topics = set()
        for note in model['notes']:
            if (not isinstance(note, dict) or note.get('topic') not in ('workflow', 'tradeoff', 'consumables_service')
                    or note['topic'] in topics
                    or note.get('kind') not in ('source_fact', 'conditional_interpretation')
                    or not all(isinstance(note.get(k), str) and note[k].strip() for k in ('text', 'condition', 'counterpoint'))):
                raise ValueError('缺适用条件/反证，或将材料升级为耐用性排名')
            refs = note.get('source_ids')
            if (not isinstance(refs, list) or not refs
                    or any(r not in sources or mid not in sources[r]['models'] for r in refs)):
                raise ValueError('取舍缺来源或来源不适用于该型号')
            topics.add(note['topic'])
    if seen != MODELS:
        raise ValueError('三型号比较不完整')
    if (not isinstance(data.get('shared_unknowns'), list) or not data['shared_unknowns']
            or any(not isinstance(v, str) or not v.strip() for v in data['shared_unknowns'])
            or not isinstance(data.get('low_volume_interpretation'), str) or not data['low_volume_interpretation']
            or not data.get('low_volume_source_ids')
            or any(r not in sources for r in data['low_volume_source_ids'])):
        raise ValueError('低印量解释缺来源或未知项')
    return data


def compare_case(req: PurchaseRequest, candidates: list[dict], *, path: Path = BASELINE_PATH,
                 today: date | None = None) -> dict:
    today = today or date.today()
    flags = {'purchase_recommendation_approved': False, 'transactions_enabled': False,
             'independent_content_review': 'pending', 'independent_durability_evidence_count': 0}
    bounds = monthly_page_bounds(req)
    if (req.category != 'printer' or req.needs_color is not False or req.accepts_outsourced_color is not True
            or bounds is None or not 0 <= bounds[0] <= bounds[1] <= 50 or req.budget_max_cny != 1000):
        return {'status': 'case_not_applicable', 'models': [], **flags}
    try:
        data = load_case_baseline(path, today=today)
    except (ValueError, TypeError, KeyError, OSError):
        return {'status': 'baseline_unavailable_or_invalid', 'models': [], **flags}
    by_id = {c['model_id']: c for c in candidates}
    source_map = {s['id']: s for s in data['sources']}
    rows = []
    for model in data['models']:
        candidate = by_id.get(model['model_id'])
        if candidate is None:
            continue
        rows.append({'model_id': model['model_id'], 'name': candidate['name'],
                     'constraint_assessment': ('excluded_by_required_condition' if candidate['required_failed'] else
                                               'required_conditions_unresolved' if candidate['required_unknown'] else
                                               'continue_verification_not_purchase_approved'),
                     'required_failed': candidate['required_failed'], 'required_unknown': candidate['required_unknown'],
                     'notes': [{**{k:n[k] for k in ('topic', 'kind', 'text', 'condition', 'counterpoint', 'source_ids')},
                                'sources': [{k: source_map[r][k] for k in SOURCE_FIELDS}
                                               for r in n['source_ids']]} for n in model['notes']],
                     'purchasable': False})
    return {'status': 'limited_manual_case_comparison', 'case_id': data['case_id'],
            'baseline_recorded_on': data['recorded_on'], 'scope': data['scope'], 'models': rows,
            'baseline_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'baseline_needs_recheck': (today - date.fromisoformat(data['recorded_on'])).days > 30,
            'shared_unknowns': data['shared_unknowns'], 'low_volume_interpretation': data['low_volume_interpretation'],
            'low_volume_sources': [{k:source_map[r][k] for k in SOURCE_FIELDS} for r in data['low_volume_source_ids']],
            'notice': '执行者人工基线：资料事实与项目条件性解释分列；逐候选硬条件优先；未批准购买或耐用性结论', **flags}
