"""Local-only replay of the unified rule/model/manual publication gate."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shopping_decision.claim_gate import publish_checked_comparison, validate_research_claims


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    incoming = json.loads(args.input.read_text(encoding="utf-8"))
    if "bundle" in incoming and "model_result" in incoming:
        result = publish_checked_comparison(incoming["bundle"], incoming["model_result"], origin="model")
    elif incoming.get("schema_version") == 1 and "requirements" in incoming:
        result = publish_checked_comparison(incoming, origin="rule")
    elif isinstance(incoming.get("candidates"), list) and "fixed_user_input" in incoming:
        result = validate_research_claims(incoming)
    else:
        parser.error("unsupported input schema")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x", encoding="utf-8") as output:
        json.dump(result, output, ensure_ascii=False, indent=2, allow_nan=False)
        output.write("\n")
    print(json.dumps({"status": "written", "origin": result["origin"],
                      "claim_count": len(result["claims"]), "path": str(args.out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
