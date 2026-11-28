"""Four sensitivity challenges using the same paired replayer and frozen reference."""
import copy,json,tempfile
from pathlib import Path
from paired_replay import EX,TASK,REF,load,save,ref,populate,basis,comparable,replay,checker,submit_message
def main():
    folder=EX/"formal-challenges-v2";folder.mkdir(exist_ok=False)
    refs={r["case_id"]:r for r in load(REF)["cases"]};r=refs["T02"]
    limits=load(TASK/"TASK_CASES.json")["limits"]
    cases=[]
    with tempfile.TemporaryDirectory(prefix="focus-challenges-") as d:
        base=Path(d);populate(base,"baseline");b=basis(base,limits)
        a=replay(base,folder/"aa1",r,b);same=replay(base,folder/"aa2",r,b)
        identical=a["metrics"]==same["metrics"] and not a["trace_errors"] and not same["trace_errors"] and a["semantic_completed"] and same["semantic_completed"]
        cases.append(dict(id="CH01",expected="same version, same answer counts and outcome",observed=dict(a=a["metrics"],b=same["metrics"]),detected=identical,raw_artifacts=[a["arm"]["replay"],same["arm"]["replay"],ref(REF)]))
        hidden=copy.deepcopy(r);hidden["initial_state"]=submit_message(hidden["initial_state"],"needs_color","是")
        h=replay(base,folder/"hidden",hidden,b);c=checker();c.inspect(h["arm"],r)
        cases.append(dict(id="CH03",expected="unasked answer injected into initial state rejected",observed=c.errors[:],detected="hidden answer/state injection" in c.errors,raw_artifacts=[h["arm"]["replay"],ref(REF)]))
        wrong=base/"shopping_decision/chat_bridge.py";old=wrong.read_text(encoding="utf8")
        needle='    editable = "\\n".join'
        assert old.count(needle)==1
        insert='    if v.get("category") == "printer" and "needs_color" not in v:\n        active = "" if "budget_max_cny" in state.get("deferred_fields", []) else "budget_max_cny"\n        prompt = QUESTION["budget_max_cny"] if active else "测试故意阻断"\n        choices = REFS["budget_max_cny"] if active else []\n'
        wrong.write_text(old.replace(needle,insert+needle),encoding="utf8")
        mutant=save(folder/"mutation.json",dict(file="shopping_decision/chat_bridge.py",insert=insert,only_isolated_copy=True))
        bad=replay(base,folder/"wrong-question",r,b)
        cases.append(dict(id="CH02",expected="irrelevant answer and unmet route goal",observed=bad["metrics"],detected=not bad["metrics"]["completed"] and bad["metrics"]["irrelevant"]>=1,raw_artifacts=[bad["arm"]["replay"],mutant,ref(REF)]))
        # Actual file changes, not merely different claimed source labels.
        reg=base/"knowledge/printer_cognition_guide_v1.json";data=load(reg)
        before=save(folder/"registry-before.json",data)
        data["sources"]["hp-cn-home"]["revision"]=2
        after=save(folder/"registry-after.json",data);reg.write_text(json.dumps(data,ensure_ascii=False),encoding="utf8")
        changed=basis(base,limits)
        fewer=copy.deepcopy(limits);fewer["max_answer_turns"]-=1
        changed_resource=copy.deepcopy(b);changed_resource["limits"]=fewer
        obs=dict(common_comparable=comparable(b,b),source_comparable=comparable(b,changed),resource_comparable=comparable(b,changed_resource),a=b,b=changed,resource=changed_resource)
        evidence=save(folder/"comparison-basis.json",obs)
        cases.append(dict(id="CH04",expected="real source bytes and resource budget mismatch are incomparable",observed=obs,detected=obs["common_comparable"] and not obs["source_comparable"] and not obs["resource_comparable"],raw_artifacts=[before,after,evidence,a["arm"]["replay"]]))
    save(EX/"challenge-results.json",dict(cases=cases,limit="frozen reference T02 sensitivity; repeat after final replayer modifications"))
    for x in cases:print(x["id"],x["detected"],flush=True)
    if not all(x["detected"] for x in cases):raise SystemExit(1)
if __name__=="__main__":main()
