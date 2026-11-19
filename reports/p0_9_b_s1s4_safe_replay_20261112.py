"""安全复跑旧24项独立反例：旧评估JSON不可覆盖，输出存到新路径。"""
from pathlib import Path
from unittest.mock import patch
import argparse
import runpy

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / "reports/p0_9_b_independent_20261112.json"
SCRIPT = ROOT / "reports/p0_9_b_independent_20261112.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path,
                        default=ROOT / "reports/p0_9_b_s1s4_replay_20261112.json")
    args = parser.parse_args()
    target = args.output if args.output.is_absolute() else ROOT / args.output
    if target.resolve() == OLD.resolve():
        parser.error("修补回归禁止覆盖历史独立评估结果")
    before = OLD.read_bytes()
    original_write = Path.write_text

    def safe_write(path: Path, data: str, *a, **kw):
        return original_write(target if path.resolve() == OLD.resolve() else path,
                              data, *a, **kw)

    code = 0
    with patch.object(Path, "write_text", safe_write):
        try:
            runpy.run_path(str(SCRIPT), run_name="__main__")
        except SystemExit as exc:
            code = int(exc.code or 0)
    if OLD.read_bytes() != before:
        raise RuntimeError("历史独立诊断文件被意外改变")
    if not target.is_file():
        raise RuntimeError("修补复验没有产生新机器结果")
    print("修补复验另存:", target)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
