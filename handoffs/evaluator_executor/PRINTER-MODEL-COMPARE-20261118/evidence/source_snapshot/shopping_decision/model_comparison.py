"""Explicit CLI model inference; defaults to offline rules and never reads credentials."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from .evidence_comparison import build_prompt, digest, response_schema, rule_comparison, validate_model_result


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def codex_inference(bundle, output_dir, *, timeout=120, model=None):
    """One actual inference attempt, isolated from the repository and without model tools."""
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    prompt = build_prompt(bundle)
    write_json(output_dir / "request.json", bundle)
    (output_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    executable = shutil.which("codex")
    if executable is None:
        write_json(output_dir / "meta.json", {"status": "provider_unavailable", "live_attempt": False})
        raise RuntimeError("codex_executable_unavailable")
    started = utc_now()
    with tempfile.TemporaryDirectory(prefix="shopping-model-") as scratch:
        scratch = Path(scratch)
        schema = scratch / "response.schema.json"
        schema.write_text(json.dumps(response_schema(bundle), ensure_ascii=False), encoding="utf-8")
        response_path = scratch / "response.json"
        argv = [executable, "exec", "--ignore-user-config", "--ephemeral", "--skip-git-repo-check",
                "--sandbox", "read-only", "--color", "never", "--json", "-C", str(scratch),
                "--output-schema", str(schema), "--output-last-message", str(response_path),
                "-c", 'web_search="disabled"']
        for feature in ("shell_tool", "unified_exec", "apps", "plugins", "multi_agent", "browser_use",
                        "computer_use", "image_generation", "hooks", "memories"):
            argv += ["--disable", feature]
        if model:
            argv += ["--model", model]
        argv.append("-")
        raw_stdout, raw_stderr, return_code, response, failure = b"", b"", None, None, None
        try:
            process = subprocess.run(argv, input=prompt.encode("utf-8"), capture_output=True,
                                     cwd=scratch, timeout=timeout)
            raw_stdout, raw_stderr, return_code = process.stdout, process.stderr, process.returncode
            if response_path.is_file():
                response = response_path.read_bytes()
        except subprocess.TimeoutExpired as exc:
            raw_stdout, raw_stderr, failure = exc.stdout or b"", exc.stderr or b"", "timeout"
        finished = utc_now()
    (output_dir / "stdout.events.jsonl").write_bytes(raw_stdout)
    (output_dir / "stderr.log").write_bytes(raw_stderr)
    if response is not None:
        (output_dir / "response.json").write_bytes(response)
    events = []
    for line in raw_stdout.decode("utf-8", errors="replace").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            failure = failure or "invalid_event_stream"
    tool_events = [e for e in events if isinstance(e.get("item"), dict) and
                   e["item"].get("type") not in ("agent_message", "reasoning", "error", "todo_list")]
    if tool_events:
        failure = "unexpected_model_tool_use"
    provider_errors = [e.get("error", {}).get("message", "provider_turn_failed")
                       for e in events if e.get("type") == "turn.failed"]
    if provider_errors and not failure:
        failure = str(provider_errors[-1])[:2000]
    inference_completed = any(e.get("type") == "turn.completed" for e in events)
    if not inference_completed and not failure:
        failure = "provider_did_not_complete_inference"
    usage = [e.get("usage") for e in events if e.get("type") == "turn.completed"]
    meta = {"started_at_utc": started, "finished_at_utc": finished, "command_argv": argv,
            "live_attempt": True, "input_sha256": digest(bundle), "exit_code": return_code,
            "stdout_sha256": hashlib.sha256(raw_stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(raw_stderr).hexdigest(), "usage": usage,
            "requested_model": model or "cli_default", "observed_model": "unknown", "monetary_cost": "unknown",
            "tool_event_count": len(tool_events), "inference_completed": inference_completed, "failure": failure}
    try:
        if failure or return_code != 0 or response is None:
            raise ValueError(failure or "provider_failed_or_missing_response")
        checked = validate_model_result(bundle, json.loads(response))
        write_json(output_dir / "validated.json", checked)
        meta["status"] = "accepted"
    except (ValueError, KeyError, TypeError) as exc:
        meta["status"] = "rejected"
        meta["failure"] = str(exc)
        write_json(output_dir / "meta.json", meta)
        raise RuntimeError("model_output_rejected:" + str(exc)) from exc
    write_json(output_dir / "meta.json", meta)
    return checked


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--live", action="store_true", help="explicitly use the already signed-in Codex model")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--model", help="Codex model id; select one supported by the existing account")
    args = parser.parse_args()
    bundle = json.loads(args.bundle.read_text(encoding="utf-8"))
    try:
        if args.live:
            if args.out is None:
                parser.error("--live requires a new --out directory for actual call receipts")
            result = codex_inference(bundle, args.out, model=args.model)
        else:
            result = rule_comparison(bundle)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, RuntimeError, OSError) as exc:
        print(json.dumps({"status": "failed", "reason": str(exc), "silent_fallback_used": False}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
