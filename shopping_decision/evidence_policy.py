"""H05 统一证据元数据准入：只检查可机器验证的资格，不声称核实网页内容或版权事实。"""
from __future__ import annotations
from datetime import date
from urllib.parse import urlsplit
import ipaddress

def valid_https_url(value: str) -> bool:
    if not isinstance(value, str) or not value or any(ch.isspace() or ord(ch) < 32 for ch in value):
        return False
    try:
        p = urlsplit(value)
        host = p.hostname
        if p.scheme.lower() != "https" or not host or p.username or p.password or p.port is not None:
            return False
        if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
            return False
        if "." not in host or host.startswith(".") or host.endswith("."):
            return False
        host.encode("idna")
        try:
            ip = ipaddress.ip_address(host)
            if not ip.is_global:
                return False
        except ValueError:
            pass
        return True
    except (ValueError, UnicodeError, AttributeError):
        return False

def metadata_gate(*, url: str, region: str, target_region: str, captured_on: str,
                  published_on: str | None, reviewed_on: str | None,
                  recheck_on: str | None, review_status: str,
                  allowed_uses: tuple[str, ...], purpose: str,
                  today: date, source_group: str = "") -> tuple[str, ...]:
    """返回机器可核查的拒绝理由；未拒绝也不意味着网页/结论真实。
    发布日期未知只允许在针对具体资料人工复核时处理；不允许决策级自动通过。
    """
    problems = []
    if not valid_https_url(url):
        problems.append("invalid_url")
    if not source_group:
        problems.append("missing_source_group")
    if region not in (target_region, "GLOBAL"):
        problems.append("region_mismatch")
    if review_status != "reviewed" or purpose not in allowed_uses:
        problems.append("unreviewed_or_unlicensed_use")
    try:
        captured = date.fromisoformat(captured_on)
        if captured > today:
            problems.append("future_capture")
    except (ValueError, TypeError):
        problems.append("invalid_capture_date")
    if published_on is not None:
        try:
            pub = date.fromisoformat(published_on)
            if pub > today:
                problems.append("future_publication")
            if "captured" in locals() and pub > captured:
                problems.append("publication_after_capture")
        except (ValueError, TypeError):
            if purpose == "decision_support":
                problems.append("unknown_publication")
    if not reviewed_on or not recheck_on:
        problems.append("missing_review_window")
    else:
        try:
            reviewed = date.fromisoformat(reviewed_on)
            expires = date.fromisoformat(recheck_on)
            if reviewed > today or expires < today or reviewed > expires:
                problems.append("review_out_of_window")
            if "captured" in locals() and reviewed < captured:
                problems.append("review_before_capture")
        except (TypeError, ValueError):
            problems.append("invalid_review_date")
    return tuple(dict.fromkeys(problems))
