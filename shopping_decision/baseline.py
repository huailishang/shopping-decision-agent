"""无模型、无网络、无真实 SKU 的可审计打印机选购路线基线。

这是工程契约测试，不是完整专业知识库，也不是商品购买建议。
真实证据在后续阶段接入；此处所有知识规则都标记为 synthetic。
"""

from __future__ import annotations

from .contracts import Evidence, PurchaseRequest, Recommendation


SYNTHETIC_EVIDENCE = {
    "demo-usage": Evidence(
        evidence_id="demo-usage",
        source_type="synthetic",
        claim="合成示例：低频、以黑白为主时，比较黑白激光的闲置维护与耗材成本。",
    ),
    "demo-color": Evidence(
        evidence_id="demo-color",
        source_type="synthetic",
        claim="合成示例：大量彩色输出时，重点比较彩色墨仓的单页成本与维护。",
    ),
}


def recommend_route(request: PurchaseRequest) -> Recommendation:
    """生成路线级结论；从不生成具体型号、实时价格或订单。"""
    if request.category != "printer":
        return Recommendation(
            status="unsupported",
            recommended_route=None,
            reasons=("当前合成基线只覆盖打印机品类，其他品类需接入可验证知识。",),
        )

    if request.monthly_pages is None or request.needs_color is None:
        questions: list[str] = []
        if request.monthly_pages is None:
            questions.append("每月大概打印多少页，是否经常间隔几周不使用？")
        if request.needs_color is None:
            questions.append("是否必须在家打印彩色，还是黑白就够？")
        return Recommendation(
            status="clarify",
            recommended_route=None,
            reasons=("缺少决定技术路线的关键使用条件，不能直接指定型号。",),
            questions=tuple(questions),
        )

    if not request.needs_color and request.monthly_pages <= 50:
        return Recommendation(
            status="route_recommended",
            recommended_route="monochrome_laser",
            reasons=(
                "低频且只需黑白：优先评估黑白激光路线；仍要比较粉盒、硒鼓、无线打印和售后。",
                "这是路线级选择，不代表任何品牌或型号当前有货。",
            ),
            evidence_ids=("demo-usage",),
        )

    if request.needs_color and request.monthly_pages >= 150:
        return Recommendation(
            status="route_recommended",
            recommended_route="color_ink_tank",
            reasons=(
                "较大量彩印：可优先考察墨仓路线的单页成本，但必须核对使用频次与维护。",
                "耗材单页成本不能单独替代总拥有成本。",
            ),
            evidence_ids=("demo-color",),
        )

    if request.needs_color and request.monthly_pages <= 50:
        if request.accepts_outsourced_color is None:
            return Recommendation(
                status="clarify",
                recommended_route=None,
                reasons=("虽以黑白为主，但偶尔彩色是否必须在家完成，会改变路线结论。",),
                questions=("偶尔的彩印能否去打印店完成？",),
            )
        if request.accepts_outsourced_color:
            return Recommendation(
                status="route_recommended",
                recommended_route="monochrome_laser_plus_outsource",
                reasons=(
                    "低频日常黑白 + 彩印可外包：优先比较黑白激光和偶发外包彩印的综合成本。",
                    "应核查居住地外包打印是否便利，不能直接宣称成本必然最低。",
                ),
                evidence_ids=("demo-usage", "demo-color"),
            )

    return Recommendation(
        status="compare_routes",
        recommended_route=None,
        reasons=("场景不适合直接锁定一种技术路线，需要按印量、彩印质量、维护、总成本做对照。",),
        evidence_ids=("demo-usage", "demo-color"),
    )


def assert_no_unauthorized_transaction(result: Recommendation) -> bool:
    """安全不变量：输出始终没有订单/支付副作用。"""
    return not result.authorized_side_effects and not result.product_skus and not result.live_quotes
