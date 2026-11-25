"""Task-local Windows runtime probe. No account files, no installs, no tool use."""
import json
import sys
import subprocess
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
from datetime import date

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
# parents: executor, evidence, task, evaluator_executor, handoffs, repository
sys.path.insert(0, str(ROOT))
from shopping_decision import model_comparison as adapter
from shopping_decision.evidence_comparison import rule_comparison
from shopping_decision.claim_gate import publish_checked_comparison
from shopping_decision.cognition_comparison import load_pack, DIMS

EXE = Path(r"D:\SoftWare\npm\node_modules\@openai\codex\node_modules\@openai\codex-win32-x64\vendor\x86_64-pc-windows-msvc\bin\codex.exe")
case_id = sys.argv[1]
if case_id not in ("C01", "C04", "C08"):
    raise SystemExit("unfrozen case")
model = sys.argv[2] if len(sys.argv) > 2 else None
if model not in (None, "gpt-5.4", "gpt-5.2"):
    raise SystemExit("unapproved model identifier")
if len(list(HERE.glob("native-C*"))) >= 4:
    raise SystemExit("new inference budget exhausted")
out = HERE / ("native-" + case_id + ("-" + model if model else ""))
if out.exists():
    raise SystemExit("attempt directory already exists; never repeat automatically")
cases = json.loads((HERE.parent / "cases-after.json").read_text(encoding="utf-8"))["cases"]
case = next(c for c in cases if c["case_id"] == case_id)
values = case["confirmed_fields"]
pack = load_pack()
assert pack and EXE.is_file()
sources, facts = deepcopy(pack["sources"]), deepcopy(pack["facts"])
region = values["device_deployment_region"]
for row in sources + facts:
    if row.get("scope_region") == "中国大陆":
        row["scope_region"] = region
reqs = [{"id":"cognition:"+dim,"dimension":dim,"unit":"bool","op":"eq","value":True,
         "importance":"hard" if (dim=="scan" and values.get("requires_scan") is True)
             or (dim=="auto_duplex" and values.get("requires_auto_duplex") is True)
             or (dim=="color_print" and values.get("needs_color") is True) else "soft"} for dim in DIMS]
reqs.append({"id":"confirmed:wechat_reuse","dimension":"wechat_reuse","unit":"bool","op":"eq","value":True,"importance":"hard" if values.get("wechat_required") is True else "soft"})
reqs.append({"id":"confirmed:budget","dimension":"cost","unit":"CNY","op":"lte","value":values.get("budget_max_cny",1000),"importance":"hard"})
bundle={"schema_version":1,"request_id":"printer-cognition-native-"+case_id,"category":"printer",
        "as_of":date.today().isoformat(),"region":region,
        "candidates":[{"id":"Brother HL-L1238W"},{"id":"HP M232dw"}],
        "requirements":reqs,"sources":sources,"facts":facts}
# Pass only bounded public product evidence and typed requirements.
# Preserve the same exact input for deterministic and model runs.
actual_run = subprocess.run
def isolated_run(argv, *args, **kwargs):
    if not argv or Path(argv[0]) != EXE:
        raise RuntimeError("unexpected executable")
    argv = list(argv[:-1]) + ["--disable","browser_use_external","--disable","in_app_browser",
                "-c",'approval_policy="never"',"-"]
    return actual_run(argv,*args,**kwargs)
rule=rule_comparison(bundle)
public=publish_checked_comparison(bundle,origin="rule")
print("starting bounded native inference",case_id,flush=True)
try:
    with patch.object(adapter.shutil,"which",return_value=str(EXE)),patch.object(adapter.subprocess,"run",side_effect=isolated_run):
        result=adapter.codex_inference(bundle,out,timeout=175,model=model)
    print("accepted",case_id,flush=True)
except Exception as exc:
    print("probe failed",type(exc).__name__,str(exc)[:300],flush=True)
finally:
    if out.is_dir():
        adapter.write_json(out/"rule-result.json",rule)
        adapter.write_json(out/"rule-public.json",public)
        adapter.write_json(out/"probe-constraints.json",{"native_exe":str(EXE),"extra_cli_flags":["--disable browser_use_external","--disable in_app_browser",'approval_policy="never"'],"no_user_config":True,"no_purchase_permission":True,"model_default":model is None,"requested_model":model,"case_id":case_id})
