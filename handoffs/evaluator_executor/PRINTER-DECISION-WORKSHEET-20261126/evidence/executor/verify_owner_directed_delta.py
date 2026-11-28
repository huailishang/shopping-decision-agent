"""Supplement only; never substitutes silently for frozen VP-08."""
from pathlib import Path
import hashlib,json,runpy
E=Path(__file__).resolve().parent
B=E.parents[1]
ROOT=B.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
d=json.loads((E/'R4_OWNER_DIRECTED_SCOPE.json').read_text(encoding='utf8'))
base=json.loads((B/'BASELINE.json').read_text(encoding='utf8'))
assert d['allowed_delta_paths']==['scripts/audit_model_history_readonly.py','tests/test_history_audit_version_transition.py']
assert set(d['after_sha256'])==set(d['allowed_delta_paths'])
actual=runpy.run_path(str(B/'VERIFY_SCOPE.py'))['snapshot']()
before=base['protected_files_sha256']
after=actual['protected_files_sha256']
changed=sorted(p for p in before.keys()|after.keys() if before.get(p)!=after.get(p))
checks={
'original_baseline_intact':sha(B/'BASELINE.json')==d['original_baseline_sha256']==(B/'BASELINE.sha256').read_text().strip(),
'original_plan_intact':sha(B/'VALIDATION_PLAN.yaml')==d['original_validation_plan_sha256'],
'head_unchanged':actual['baseline_head']==base['baseline_head'],
'index_unchanged':actual['index_diff_sha256']==base['index_diff_sha256'],
'original_auditor_pinned':before.get(d['allowed_delta_paths'][0])==d['original_auditor_sha256'],
'new_test_not_in_original':d['allowed_delta_paths'][1] not in before,
'exact_two_deltas':changed==sorted(d['allowed_delta_paths']),
'delta_exact_sha256':all(after.get(p)==h for p,h in d['after_sha256'].items()),
'all_product_bytes_unchanged_in_R4':actual['product_sha256']==d['before_product_sha256'],
}
result={'status':'PASS' if all(checks.values()) else 'FAIL','purpose':'owner-directed supplemental evidence, independent approval pending; does not change frozen VP-08','checks':checks,'original_protected_count':len(before),'unchanged_original_protected':sum(after.get(p)==h for p,h in before.items()),'changed_protected_paths':changed,'exact_delta_sha256':d['after_sha256']}
print(json.dumps(result,ensure_ascii=False,indent=2))
raise SystemExit(not all(checks.values()))
