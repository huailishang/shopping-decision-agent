"""复核本轮只读准备的文件绑定；不是合同验收器，不判资料许可或认知收益。"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import zipfile


def main():
    root = Path(__file__).resolve().parents[4]
    ev = Path(__file__).resolve().parent
    task = ev.parent
    read = lambda p: json.loads(p.read_text(encoding="utf-8"))
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    start = read(ev / "executor_start_snapshot.json")
    assert start["planning_count"] == start["matching_count"] == 120
    for row in start["files"]:
        assert sha(root / row["path"]) == row["actual_sha256"], row["path"]
    archive = ev / "executor_start_source_snapshot.zip"
    assert sha(archive) == start["snapshot_sha256"]
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert len(z.namelist()) == 120
        for row in start["files"]:
            assert hashlib.sha256(z.read(row["path"])).hexdigest() == row["actual_sha256"]
    base = read(ev / "baseline_capture.json")
    for field, name in (("input_sha256", "baseline_input.json"),
                        ("stdout_sha256", "baseline_cli.stdout.jsonl")):
        assert sha(ev / name) == base[field]
    sample = read(root / base["sample_path"])
    expected = {k: v for k, v in sample["normalized_project_owner_proxy_fields"].items()
                if v is not None}
    assert read(ev / "baseline_input.json")["answers"] == expected
    assert sha(root / base["sample_path"]) == base["sample_sha256"]
    actual = json.loads((ev / "baseline_cli.stdout.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    view = actual["real_printer_case_research"]["shared_research_snapshot"]
    assert {x["eligibility"] for x in view["all_candidates"]} == {"model_spec_research_only"}
    assert view["purchase_recommendation_approved"] is False
    assert view["transactions_enabled"] is False
    manifest = read(ev / "material_manifest.json")
    for row in manifest["materials"]:
        assert sha(root / row["local_allowed_excerpt_or_note_path"]) == row["local_note_sha256"]
        assert row["admitted_to_normal_chain"] is False
        if "existing_local_original" in row:
            original = row["existing_local_original"]
            assert sha(root / original["path"]) == original["sha256"]
    ledger = read(ev / "public_action_ledger.json")
    assert sum(x["kind"] == "search" for x in ledger["actions"]) == 6
    assert sum(x["kind"] != "search" for x in ledger["actions"]) == 5
    assert all(v == 0 for v in ledger["prohibited_actions"].values())
    assert read(ev / "development_comparison.json")["paired_answers_generated"] is False
    checked_files = []
    for path in task.rglob("*"):
        if path.is_file() and path.suffix in {".json", ".md", ".py"}:
            if path.suffix == ".json":
                read(path)
            if path.name.startswith("CONTRACT") or path.name == "EVALUATION_RULES.md":
                continue
            text = path.read_text(encoding="utf-8")
            assert not any(line.rstrip() != line for line in text.splitlines()), path
            checked_files.append(path.relative_to(root).as_posix())
    now = datetime.now(timezone(timedelta(hours=8)))
    observed = datetime.fromisoformat("2026-11-16T22:16:11+08:00")
    required_missing = [p for p in (
        "scripts/verify_printer_research_delivery.py",
        "tests/test_printer_research_delivery.py",
        "handoffs/evaluator_executor/HNA-RESEARCH-ADMISSION-20261116/evidence/task_register.json",
    ) if not (root / p).exists()]
    result = {
        "status": "preparation_integrity_checked_not_contract_acceptance",
        "checked_at": now.isoformat(),
        "source_hashes_unchanged": 120,
        "snapshot_entries_valid": 120,
        "material_note_shas_matched": len(manifest["materials"]),
        "old_normal_cli_output_bound": True,
        "searches": 6, "reads_including_pdf_render": 5,
        "missing_frozen_dependencies": required_missing,
        "vp01_to_vp06_run": False,
        "product_tests_or_gui_run": False,
        "independent_evaluation": False,
        "measured_session_window": {
            "first_clock_observation": observed.isoformat(),
            "checked_at": now.isoformat(),
            "wall_minutes": round((now - observed).total_seconds() / 60, 2),
            "note": "单一执行者连续准备的可测墙钟时间；此前读CURRENT等加载未单独计时。不是完整有效工时或24小时余额。",
        },
        "utf8_and_json_checked_files": checked_files,
    }
    (ev / "preparation_validation.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ("utf8_and_json_checked_files",)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
