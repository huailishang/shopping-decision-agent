"""Read-only independent review of the prefreeze delivery; writes only fresh review evidence."""
from pathlib import Path
import hashlib, json, subprocess, sys, zipfile
import fitz

ROOT = Path.cwd()
TASK = ROOT / "handoffs/evaluator_executor/HNA-RESEARCH-ADMISSION-20261116"
EV = TASK / "evidence"
OUT = EV / "independent_prefreeze_review"
def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
index = read(EV / "preparation_delivery_index.json")
artifact_checks = []
for row in index["artifacts"]:
    path = ROOT / row["path"]
    artifact_checks.append({
        "path": row["path"], "sha_matches": digest(path) == row["sha256"],
        "bytes_match": path.stat().st_size == row["bytes"]
    })
assert all(x["sha_matches"] and x["bytes_match"] for x in artifact_checks)
for name, sha in index["unchanged_contract_dependencies"].items():
    assert digest(TASK / name) == sha, name
planning = read(EV / "planning_r2_baseline.json")
assert len(planning["source_hashes"]) == 120
assert all(digest(ROOT / p) == sha for p,sha in planning["source_hashes"].items())
start = read(EV / "executor_start_snapshot.json")
with zipfile.ZipFile(EV / "executor_start_source_snapshot.zip") as archive:
    assert archive.testzip() is None and len(archive.namelist()) == 120
    assert all(hashlib.sha256(archive.read(row["path"])).hexdigest() == row["actual_sha256"]
               for row in start["files"])

manifest = read(EV / "material_manifest.json")
for row in manifest["materials"]:
    assert digest(ROOT / row["local_allowed_excerpt_or_note_path"]) == row["local_note_sha256"]
    assert row["admitted_to_normal_chain"] is False
old_meta = read(EV / "baseline_capture.json")
assert digest(EV / "baseline_input.json") == old_meta["input_sha256"]
assert digest(EV / "baseline_cli.stdout.jsonl") == old_meta["stdout_sha256"]
assert digest(ROOT / old_meta["sample_path"]) == old_meta["sample_sha256"]

pdf_info = manifest["materials"][0]["existing_local_original"]
pdf = ROOT / pdf_info["path"]
assert digest(pdf) == pdf_info["sha256"]
with fitz.open(pdf) as document:
    assert len(document) == 2
    page = document[1].get_text()
    support = {term:term in page for term in ("WPS", "常亮", "首次使用微信打印功能前需先绑定打印机")}
assert all(support.values())
# Only attest explicit statements, never infer persistence from absence.
source_support = {
    "cached_pdf_matches_old_digest": True, "page_2_explicit_statements": support,
    "repeat_print_success_proven": False, "source_is_new": False
}

ledger = read(EV / "public_action_ledger.json")
searches = [a for a in ledger["actions"] if a["kind"] == "search"]
reads = [a for a in ledger["actions"] if a["kind"] != "search"]
assert len(searches) == ledger["budget"]["search_used"] == 6
assert len(reads) == ledger["budget"]["document_reads_used"] == 5
assert len(searches) <= ledger["budget"]["search_limit"]
assert len(reads) <= ledger["budget"]["document_read_limit"]
assert all(v == 0 for v in ledger["prohibited_actions"].values())
bad_site_syntax = [a["id"] for a in searches
                   if a["input"]["q"].startswith("site.") and not a["input"]["q"].startswith("site:")]

argv = [sys.executable, "-X", "utf8", "-m", "shopping_decision.dialogue_flow", "--real-printer-case"]
proc = subprocess.run(argv, input=(json.dumps(read(EV/"baseline_input.json"), ensure_ascii=False)+"\n").encode("utf-8"),
                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60, cwd=ROOT)
OUT.mkdir(parents=True, exist_ok=True)
(OUT/"independent_cli.run02.stdout.jsonl").write_bytes(proc.stdout)
(OUT/"independent_cli.run02.stderr.log").write_bytes(proc.stderr)
assert proc.returncode == 0, proc.stderr.decode("utf-8", errors="replace")
old = json.loads((EV/"baseline_cli.stdout.jsonl").read_text(encoding="utf-8").splitlines()[-1])
new = json.loads(proc.stdout.decode("utf-8").splitlines()[-1])
old_view = old["real_printer_case_research"]["shared_research_snapshot"]
new_view = new["real_printer_case_research"]["shared_research_snapshot"]
assert old_view == new_view
assert [x["model_id"] for x in new_view["all_candidates"]] == ["HL-L1238W","M232dw"]
assert all(x["eligibility"] == "model_spec_research_only" for x in new_view["all_candidates"])
assert new_view["purchase_recommendation_approved"] is False and new_view["transactions_enabled"] is False
assert read(EV/"development_comparison.json")["paired_answers_generated"] is False
for row in index["artifacts"]:
    assert digest(ROOT/row["path"]) == row["sha256"], "old delivery was modified"
result = {
    "review_kind": "independent_prefreeze_evidence_review_not_L3_product_acceptance",
    "head": subprocess.check_output(["git","rev-parse","HEAD"], cwd=ROOT,text=True).strip(),
    "delivery_artifacts_matched": len(artifact_checks), "source_files_unchanged": 120,
    "zip_entries_verified": 120, "material_notes_matched": 3,
    "artifact_checks": artifact_checks, "cached_pdf":source_support,
    "public_ledger": {"searches":6,"reads":5,"search_limit_reached":True,
                     "counts_only_audited_not_independently_replayed":True,
                     "non_domain_operator_query_ids":bad_site_syntax,
                     "raw_search_results_present":False},
    "cli": {"argv":argv,"exit_code":proc.returncode,"stdout_bytes":len(proc.stdout),
            "archived_old_stdout_file_bytes":(EV/"baseline_cli.stdout.jsonl").stat().st_size,
            "shared_snapshot_equal":True, "full_json_equal":old == new,
            "output_sha256":hashlib.sha256(proc.stdout).hexdigest(),
            "eligibilities":[{"model":x["model_id"],"status":x["eligibility"]} for x in new_view["all_candidates"]],
            "next_action":new_view.get("next_action")},
    "new_materials_in_normal_chain":0,"paired_effect_measured":False,
    "external_calls_this_review":0,"credentials_read_this_review":0,
    "purchase_recommendation_approved":False,"transactions_enabled":False,
    "old_delivery_files_unchanged":True
}
print(json.dumps(result, ensure_ascii=True,indent=2))
