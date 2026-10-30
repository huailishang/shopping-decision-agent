"""运行：python -m shopping_decision.demo"""

from dataclasses import asdict
import json

from .baseline import recommend_route, assert_no_unauthorized_transaction
from .contracts import PurchaseRequest


def main() -> None:
    request = PurchaseRequest(
        category="printer",
        budget_max_cny=1000,
        monthly_pages=30,
        needs_color=True,
        accepts_outsourced_color=None,
        requirements=("可靠", "易维护", "手机打印"),
    )
    result = recommend_route(request)
    assert assert_no_unauthorized_transaction(result)
    print(json.dumps({
        "mode": "synthetic_contract_demo_only",
        "request": asdict(request),
        "decision": asdict(result),
        "external_api_connected": False,
        "real_purchase_enabled": False,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
