from unittest import TestCase
from shopping_decision.cognition_comparison import replacement_count,lifecycle_cost,compare_lifecycle_costs
class LifecycleTests(TestCase):
    def test_zero_boundary_and_sensitivity(self):
        self.assertEqual(replacement_count(0,0,1500),0)
        self.assertEqual(replacement_count(1500,1500,1500),0)
        self.assertEqual(replacement_count(1501,1500,1500),1)
        self.assertEqual(replacement_count(1800,0,1500),2)
        self.assertEqual(replacement_count(1800,0,600),3)
        for bad in ((1,None,1500),(1,0,0),(True,0,1)):
            with self.assertRaises(ValueError):replacement_count(*bad)

    def test_scenario_drum_dedup_and_flip(self):
        a=dict(pages=1800,hardware=500,starter=0,toner_yield=1500,toner_price=100,
               separate_drum=True,drum_yield=10000,drum_price=200,maintenance=0)
        b=dict(a,hardware=550,separate_drum=False,toner_price=50)
        x=lifecycle_cost(**a);y=lifecycle_cost(**b)
        self.assertEqual(x["total"],"700")
        self.assertEqual(y["total"],"650")
        self.assertEqual(y["drum_replacements"],0)
        self.assertEqual(compare_lifecycle_costs(x,y),"b")
        self.assertEqual(compare_lifecycle_costs(lifecycle_cost(**dict(a,starter=1500)),y),"a")
        self.assertIsNone(lifecycle_cost(**dict(a,maintenance=None)))
        self.assertEqual(compare_lifecycle_costs(None,y),"unknown")
        self.assertEqual(lifecycle_cost(**dict(a,pages=10001))["drum_replacements"],1)

    def test_new_maintenance_evidence_withdrawal(self):
        from shopping_decision import cognition_comparison as cog
        from unittest.mock import patch
        from datetime import date
        pack=cog.load_pack()
        values={"category":"printer","usage":"低频家庭","monthly_pages_range":[0,50],
                "needs_color":False,"device_deployment_region":"中国大陆河南省",
                "wechat_required":True,"wechat_workflow":"miniprogram","budget_max_cny":1000}
        current=cog.compare(values,1,date(2026,11,26))
        self.assertTrue(current["decision"]["cost_scenario"]["models"]["HP M232dw"]["replace_on_unacceptable_quality"])
        self.assertIn("不能仅因低告警就计入一次更换成本",cog.render(current,values))
        next(s for s in pack["sources"] if s["id"]=="hp-cn-maintenance-guide-20261126")["revoked"]=True
        with patch.object(cog,"load_pack",return_value=pack):
            changed=cog.compare(values,1,date(2026,11,26))
        self.assertIsNone(changed["decision"]["cost_scenario"]["models"]["HP M232dw"]["replace_on_unacceptable_quality"])
        self.assertNotIn("不能仅因低告警就计入一次更换成本",cog.render(changed,values))
