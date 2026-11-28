import unittest,json
from pathlib import Path
from copy import deepcopy
from shopping_decision.evidence_snapshot import snapshot_valid
from shopping_decision.evidence_comparison import digest
def evidence():
    d=json.loads(Path('knowledge/printer_cognition_comparison_v1.json').read_text(encoding='utf8'))
    s=next(s for s in d['sources'] if s.get('snapshot'))
    f=next(f for f in d['facts'] if f['id']==s['snapshot']['body']['fact']['id'])
    return s,f
class SnapshotLineage(unittest.TestCase):
    def test_snapshot(self):
        s,f=evidence();self.assertTrue(snapshot_valid(s,f))
    def test_tamper(self):
        s,f=evidence();s['snapshot']['body']['excerpt']+='x'
        self.assertFalse(snapshot_valid(s,f))
    def test_revoke(self):
        s,f=evidence();s['revoked']=True
        self.assertFalse(snapshot_valid(s,f))
    def test_wrong_fact(self):
        s,f=evidence();f['candidate_id']='other'
        self.assertFalse(snapshot_valid(s,f))
    def test_wrong_excerpt_hash(self):
        s,f=evidence();s['snapshot']['body']['excerpt_sha256']='0'*64
        s['snapshot']['sha256']=digest(s['snapshot']['body'])
        self.assertFalse(snapshot_valid(s,f))
