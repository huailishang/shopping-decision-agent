"""打印机型号标识的窄范围公共规则。

支持既有 Brother 前缀型号及本案例中的 HP M232dw 系列。
提取只用于线索匹配，不证明商品身份、销售配置或平台 SKU。
"""
from __future__ import annotations

import re

MODEL_PATTERN = re.compile(
    r"(?<![A-Z0-9])(?:"
    r"(?:HL|DCP|MFC|FAX|PT|QL|ADS)-?[A-Z0-9]{2,40}"
    r"|M[0-9]{3}[A-Z]{0,3}"
    r")(?![A-Z0-9])",
    re.IGNORECASE,
)


def extract_model_tokens(value: object) -> list[str]:
    if not isinstance(value, str):
        return []
    return sorted({match.upper() for match in MODEL_PATTERN.findall(value)})


def is_model_token(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    matches = extract_model_tokens(value)
    return len(matches) == 1 and matches[0] == value.upper()


def exact_model_in_text(text: object, model: object) -> bool:
    if not isinstance(model, str) or not is_model_token(model):
        return False
    return model.upper() in extract_model_tokens(text)
