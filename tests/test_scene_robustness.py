import json
import unittest
from copy import deepcopy
from shopping_decision.chat_bridge import new_dialogue, submit_message, render_chat

class SceneRobustness(unittest.TestCase):
    def check_scene(self, usage, field):
        state = submit_message(submit_message(new_dialogue(), 'category', '打印机'), 'usage', usage)
        snapshot = deepcopy(state)
        view = render_chat(state)
        focus = json.loads(view['guidance_focus_json'])
        self.assertEqual(view['prompt_field'], field)
        self.assertEqual(focus['field'], field)
        self.assertEqual(focus['question'], view['prompt'])
        self.assertEqual(state, snapshot)
        self.assertNotIn(field, state['answers'])
        self.assertFalse(focus['transactions_enabled'])
        self.assertFalse(focus['purchase_recommendation_approved'])
        deferred = submit_message(state, field, '暂不确定')
        self.assertNotEqual(render_chat(deferred)['prompt_field'], field)

    def test_positive(self):
        for usage, field in [('把纸本收据做成电子版','requires_scan'), ('正反都要印，不想手动操作','requires_auto_duplex'), ('旅行三个月，回来再打印','idle_weeks_pattern')]:
            with self.subTest(usage=usage): self.check_scene(usage, field)

    def test_negation(self):
        for usage, field in [('无需复印，主要想让机器自动翻纸','requires_auto_duplex'), ('不想双面，主要把纸质票据转成PDF','requires_scan'), ('不考虑微信，担心几个月不用','idle_weeks_pattern')]:
            with self.subTest(usage=usage): self.check_scene(usage, field)

    def test_ambiguity(self):
        for usage, field in [('扫描是不是必要，还不确定','requires_scan'), ('微信可能方便','wechat_required'), ('主机耗材预算尚未想好','budget_scope')]:
            with self.subTest(usage=usage): self.check_scene(usage, field)
