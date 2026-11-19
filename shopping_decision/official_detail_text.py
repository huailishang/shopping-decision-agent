"""官网详情只读抽取：保守处理 DOM 归属、隐藏样式和型号作用域。"""
from __future__ import annotations

import re
from html.parser import HTMLParser

_SKIP = frozenset(("script", "style", "noscript", "template", "svg"))
_VOID = frozenset(("br", "img", "input", "meta", "link", "hr", "source", "wbr", "area", "embed"))
_BLOCK = frozenset(("p", "div", "section", "article", "aside", "h1", "h2", "h3", "h4", "li", "ul", "ol", "table", "tr", "footer", "header"))
_NEGATIVE = re.compile(r"(?:不支持|未支持|不兼容|不具备|无法使用|不能使用|不提供|不含|未配置)")
_MODEL = re.compile(r"(?<![A-Z0-9])(?:HL|DCP|MFC|FAX|PT|QL|ADS)-?[A-Z0-9-]{3,}(?![A-Z0-9])", re.IGNORECASE)
_CSS_RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")
_CSS_HIDDEN = re.compile(
    r"(?:\bdisplay\s*:\s*none\b|\bvisibility\s*:\s*hidden\b|"
    r"\bcontent-visibility\s*:\s*hidden\b|"
    r"\bopacity\s*:\s*0(?:\.0+)?(?=\s*(?:;|!important\b|$)))",
    re.IGNORECASE,
)
_CLAUSE_BOUNDARY = re.compile(r"[。！？；;\n]")
_OTHER_MODEL_SCOPE = re.compile(r"(?:仅适用于|仅适用|仅限|适用于)\s*(?:其他型号|其它型号|别的型号)")
_SIMPLE = re.compile(r"(?:[a-z][\w-]*)?(?:(?:[.#][\w-]+)|(?:\[[\w-]+(?:=(?:\"[^\"]*\"|'[^']*'|[\w-]+))?\]))*", re.IGNORECASE)
_PART = re.compile(r"([.#][\w-]+|\[[\w-]+(?:=(?:\"[^\"]*\"|'[^']*'|[\w-]+))?\])", re.IGNORECASE)


def _parse_selector(selector: str):
    """仅支持标签、复合 class/id、属性及后代选择器；其他语法不默许。"""
    steps = []
    for token in selector.strip().split():
        if not token or not _SIMPLE.fullmatch(token):
            return None
        prefix = re.match(r"[a-z][\w-]*", token, re.IGNORECASE)
        tag = prefix.group(0).lower() if prefix else None
        conditions = []
        for m in _PART.finditer(token):
            term = m.group(0)
            if term[0] == ".":
                conditions.append(("class", term[1:]))
            elif term[0] == "#":
                conditions.append(("id", term[1:]))
            else:
                inside = term[1:-1]
                name, _, value = inside.partition("=")
                conditions.append(("attr", name.lower(), value.strip("\"'") if value else None))
        steps.append((tag, conditions))
    return tuple(steps) if steps else None


def _hidden_selectors(source: str):
    parsed = []
    uncertain = False
    for css in re.findall(r"<style\b[^>]*>(.*?)</style\s*>", source, flags=re.IGNORECASE | re.DOTALL):
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
        for selector_group, declarations in _CSS_RULE.findall(css):
            if not _CSS_HIDDEN.search(declarations):
                continue
            for selector in selector_group.split(","):
                steps = _parse_selector(selector)
                if steps is None:
                    uncertain = True
                else:
                    parsed.append(steps)
    return parsed, uncertain


def _matches_simple(node: tuple[str, dict], simple) -> bool:
    tag, attrs = node
    target_tag, conditions = simple
    if target_tag and tag != target_tag:
        return False
    classes = str(attrs.get("class") or "").split()
    for condition in conditions:
        if condition[0] == "class" and condition[1] not in classes:
            return False
        if condition[0] == "id" and str(attrs.get("id") or "") != condition[1]:
            return False
        if condition[0] == "attr":
            if condition[1] not in attrs:
                return False
            if condition[2] is not None and str(attrs[condition[1]]) != condition[2]:
                return False
    return True


def _matches_path(path: list[tuple[str, dict]], selector) -> bool:
    if not path or not _matches_simple(path[-1], selector[-1]):
        return False
    pos = len(path) - 2
    for step in reversed(selector[:-1]):
        while pos >= 0 and not _matches_simple(path[pos], step):
            pos -= 1
        if pos < 0:
            return False
        pos -= 1
    return True


class VisibleText(HTMLParser):
    """从可见节点提取文本，并保留块边界供型号归属与跨句更正判断。"""

    def __init__(self, source: str = ""):
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._stack: list[tuple[str, bool, dict]] = []
        self._selectors, self.visibility_uncertain = _hidden_selectors(source)

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attrs = {k.lower(): v for k, v in attrs}
        parent_hidden = self._stack[-1][1] if self._stack else False
        path = [(name, attr) for name, _, attr in self._stack] + [(tag, attrs)]
        hidden = (
            parent_hidden or tag in _SKIP or "hidden" in attrs
            or str(attrs.get("aria-hidden", "")).lower() == "true"
            or bool(_CSS_HIDDEN.search(re.sub(r"/\*.*?\*/", "", attrs.get("style") or "", flags=re.DOTALL)))
            or any(_matches_path(path, rule) for rule in self._selectors)
        )
        if tag not in _VOID:
            self._stack.append((tag, hidden, attrs))
        elif tag == "br" and not hidden:
            self.parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag.lower() not in _VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        tag = tag.lower()
        for index in range(len(self._stack) - 1, -1, -1):
            if self._stack[index][0] == tag:
                hidden = self._stack[index][1]
                del self._stack[index:]
                if tag in _BLOCK and not hidden:
                    self.parts.append("\n")
                break

    def handle_data(self, data):
        if not (self._stack and self._stack[-1][1]):
            text = " ".join(data.split())
            if text:
                self.parts.append(text)

    def text(self) -> str:
        # 连续块是不同主张作用域；不要把其他型号标题和本型号功能压成一句。
        return " ".join(self.parts)


def _claim_clause(text: str, start: int, end: int) -> str:
    left = 0
    right = len(text)
    for match in _CLAUSE_BOUNDARY.finditer(text, 0, start):
        left = match.end()
    match = _CLAUSE_BOUNDARY.search(text, end)
    if match:
        right = match.start()
    return text[left:right].strip()


def _explicit_current_comparison(clause: str, model: str) -> bool:
    return bool(re.search(
        r"与\s*(?:HL|DCP|MFC|FAX|PT|QL|ADS)-[A-Z0-9-]+\s*相比\s*[,，]?\s*"
        + re.escape(model) + r"\s*(?:同样|也)\s*", clause, re.IGNORECASE
    ))


def _scope_is_other(main: str, start: int, model: str) -> bool:
    """没有明确主体的短段落继承最近的型号小节标题，而非页面主标题。"""
    # 在主内容内有界回看，保留跨多个说明段落的最近型号标题；不回溯整页导航。
    for block in reversed(main[max(0, start - 1200):start].split("\n")[-30:]):
        block = block.strip()
        if not block:
            continue
        names = {name.upper() for name in _MODEL.findall(block)}
        if names:
            return model.upper() not in names
    return False


def _has_current_negative(main: str, model: str, feature_hint: str) -> bool:
    """否定词与本功能必须同一句、且允许“无线网络连接不支持”的后置否定。"""
    negative = r"(?:不支持|未支持|不兼容|不具备|无法使用|不能使用|不提供|不含|未配置)"
    feature = re.escape(feature_hint)
    pattern = re.compile(
        negative + r"[^。！？；;\n]{0,18}" + feature + r"|" +
        feature + r"(?:网络连接|小程序打印|小程序|打印|功能)?\s*" + negative, re.IGNORECASE
    )
    for match in pattern.finditer(main):
        clause = _claim_clause(main, match.start(), match.end())
        names = {name.upper() for name in _MODEL.findall(clause)}
        if names and model.upper() not in names:
            continue
        if not names and _scope_is_other(main, match.start(), model):
            continue
        return True
    return False


def supported_phrase(main: str, phrases: tuple[str, ...], *, model: str, feature_hint: str) -> str | None:
    """取有依据的正向事实；否定/事后限定/型号冲突返回未知，不从首个匹配直接放行。"""
    if _has_current_negative(main, model, feature_hint):
        return None
    for phrase in phrases:
        for match in re.finditer(re.escape(phrase), main, flags=re.IGNORECASE):
            clause = _claim_clause(main, match.start(), match.end())
            # 疑问、假设和操作前提不证明设备真的具备此项功能。
            if re.search(r"(?:是否|能否|可否|有没有|是不是).{0,36}" + re.escape(phrase), clause):
                continue
            if re.search(r"(?:如果|假如|假设|倘若|若|一旦).{0,35}" + re.escape(phrase), clause):
                continue
            models = {value.upper() for value in _MODEL.findall(clause)}
            if any(value != model.upper() for value in models):
                if not _explicit_current_comparison(clause, model):
                    continue
            if _OTHER_MODEL_SCOPE.search(clause):
                continue
            if not models and _scope_is_other(main, match.start(), model):
                continue
            # 后一句可能反向限定前面整段功能，不得因先见到肯定就放行。
            following = main[match.end():match.end() + 140]
            if re.search(r"(?:以上(?:功能|描述|内容)?|上述(?:功能|内容)?).{0,15}(?:仅适用|仅限)", following):
                continue
            prefix = main[max(0, match.start() - 90):match.start()]
            if re.search(r"(?:不|未|无|非|没|不可|不能|无法|不再)\s*$", prefix):
                continue
            return phrase
    return None
