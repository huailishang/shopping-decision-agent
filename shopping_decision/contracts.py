"""领域对象与外部适配器契约：默认无真实交易副作用。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, Literal


@dataclass(frozen=True)
class PriceObservation:
    """输入端看到的历史或声称当前的报价。未经授权平台核查一律不视为实时价格。"""
    sku: str
    price_minor: int
    currency: str
    observed_on: str
    source_url: str
    claims_current: bool = False


@dataclass(frozen=True)
class PurchaseRequest:
    category: str
    budget_max_cny: int | None = None
    monthly_pages: int | None = None
    needs_color: bool | None = None
    accepts_outsourced_color: bool | None = None
    requirements: tuple[str, ...] = ()
    idle_weeks: int | None = None
    requires_wireless: bool | None = None
    requires_scan: bool | None = None
    market_region: str = "CN"
    observed_price: PriceObservation | None = None
    model_id: str | None = None


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    source_type: Literal["official", "test", "expert", "review", "promotion", "synthetic"]
    claim: str
    url: str | None = None
    captured_on: str | None = None
    sponsored: bool = False


@dataclass(frozen=True)
class Recommendation:
    status: Literal["clarify", "route_recommended", "compare_routes", "unsupported", "invalid", "defer"]
    recommended_route: str | None
    reasons: tuple[str, ...]
    questions: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    product_skus: tuple[str, ...] = ()
    live_quotes: tuple[dict, ...] = ()
    authorized_side_effects: tuple[str, ...] = ()
    unknowns: tuple[str, ...] = ()
    alternative_routes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProductSnapshot:
    platform: str
    product_id: str
    sku_id: str
    recorded_at: str
    specs: dict[str, str] = field(default_factory=dict)
    price_minor: int | None = None
    source_url: str | None = None


class CategoryKnowledgeProvider(Protocol):
    """百度开放知识服务、人工审核的知识卡或合成知识库都应实现此协议。"""

    def retrieve(self, category: str, query: str) -> list[Evidence]: ...


class ProductCatalog(Protocol):
    """京东、淘宝、离线商品快照的只读适配器。"""

    def search(self, query: str) -> list[ProductSnapshot]: ...


class BenchmarkAdapter(Protocol):
    """双基准统一载入任务，但保留各自官方 gold 与指标。"""

    def load_cases(self) -> list[dict]: ...
    def evaluate(self, outputs: list[dict]) -> dict: ...
