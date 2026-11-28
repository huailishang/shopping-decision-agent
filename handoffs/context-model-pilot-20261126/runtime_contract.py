"""Domain-neutral offline candidate contract. No networking, credentials or retry."""
from dataclasses import dataclass
import json
import hashlib

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)

def fingerprint(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()

@dataclass(frozen=True)
class ModelRoute:
    provider: str
    model: str
    protocol: str
    context_window: int
    max_output: int
    reasoning_fields: tuple = ()
    # Values are exact-route configuration, not inferred from brand.

    def __post_init__(self):
        if self.protocol not in ("responses", "chat_completions") or not self.provider or not self.model:
            raise ValueError("unsupported_route")
        if type(self.context_window) is not int or type(self.max_output) is not int or not 0 < self.max_output < self.context_window:
            raise ValueError("invalid_capacity")
        if any(k not in ("reasoning", "reasoning_effort", "enable_thinking", "thinking") for k, _ in self.reasoning_fields):
            raise ValueError("unsupported_reasoning_field")
        if len(dict(self.reasoning_fields)) != len(self.reasoning_fields):
            raise ValueError("duplicate_reasoning_field")

def byte_estimate(text):
    # Conservative proxy, not an exact provider tokenizer; envelope headroom is separate.
    return len(text.encode("utf-8"))

def assemble(required, optional, route, *, input_cap, output_cap, headroom=256, meter=byte_estimate):
    if not all(type(n) is int and n > 0 for n in (input_cap, output_cap, headroom)):
        raise ValueError("invalid_budget")
    if output_cap > route.max_output:
        raise ValueError("output_cap_exceeds_route")
    cap = min(input_cap, route.context_window - output_cap - headroom)
    packet = {"required": required, "optional": {}}
    size = meter(canonical(packet))
    if size > cap:
        raise ValueError("required_context_over_budget")
    omitted = []
    for key, value in optional.items():
        candidate = {"required": required, "optional": dict(packet["optional"], **{key: value})}
        if meter(canonical(candidate)) <= cap:
            packet = candidate
        else:
            omitted.append({"id": key, "reason": "input_budget", "sha256": fingerprint(value)})
    return packet, {"input_estimate": meter(canonical(packet)), "meter": getattr(meter, "__name__", "custom"),
                    "input_cap": cap, "output_cap": output_cap, "headroom": headroom,
                    "packet_sha256": fingerprint(packet), "omitted": omitted}

def request_payload(route, system, packet, output_cap, *, meter=byte_estimate, headroom=256, input_cap=None):
    if type(output_cap) is not int or not 0 < output_cap <= route.max_output:
        raise ValueError("invalid_output_cap")
    data = canonical(packet)
    fields = dict(route.reasoning_fields)
    if route.protocol == "responses":
        payload = {"model": route.model, "instructions": system, "input": data,
                   "max_output_tokens": output_cap, "stream": False, **fields}
    else:
        payload = {"model": route.model, "messages": [{"role": "system", "content": system},
                   {"role": "user", "content": data}], "max_tokens": output_cap, "stream": False, **fields}
    estimated = meter(canonical(payload))
    if input_cap is not None and (type(input_cap) is not int or input_cap <= 0 or estimated > input_cap):
        raise ValueError("wire_input_over_budget")
    if estimated + output_cap + headroom > route.context_window:
        raise ValueError("wire_context_over_budget")
    return payload

def normalize(route, http_status=None, body=None, transport_error=None):
    """One attempt; no retries, no classification of ambiguous failures as quota."""
    result = {"provider": route.provider, "model": route.model, "protocol": route.protocol,
              "http_status": http_status, "status": None, "text": None, "usage": None,
              "provider_code": None, "retry_hint": "manual_review"}
    def finish(status, hint="manual_review", text=None):
        return dict(result, status=status, retry_hint=hint, text=text)
    if transport_error:
        return finish("timeout" if transport_error == "timeout" else "transport_error", "bounded_if_authorized")
    try:
        data = json.loads(body) if isinstance(body, (str, bytes)) else body
    except (ValueError, UnicodeError):
        data = None
    if isinstance(data, dict):
        error = data.get("error")
        result["provider_code"] = (error.get("code") if isinstance(error, dict) else None) or data.get("code")
        if isinstance(data.get("usage"), dict):
            result["usage"] = data["usage"]
    if http_status == 429:
        return finish("rate_or_quota_limit")
    if http_status in (401, 403):
        return finish("auth_or_permission")
    if http_status == 400:
        code = result["provider_code"]
        return finish("context_limit" if code in ("context_length_exceeded", "max_context_length_exceeded") else "invalid_request")
    if http_status is not None and http_status >= 500:
        return finish("provider_error", "bounded_if_authorized")
    if http_status != 200:
        return finish("unexpected_http_status")
    if not isinstance(data, dict):
        return finish("malformed_response")
    if data.get("success") is False or data.get("error"):
        return finish("provider_error")
    if data.get("model") and data["model"] != route.model:
        return finish("model_mismatch")
    if route.protocol == "responses":
        if data.get("status") == "incomplete":
            reason = data.get("incomplete_details") or {}
            return finish("output_limit" if isinstance(reason, dict) and reason.get("reason") == "max_output_tokens" else "incomplete")
        if data.get("status") != "completed" or not isinstance(data.get("output"), list):
            return finish("incomplete")
        pieces = []
        for item in data["output"]:
            if not isinstance(item, dict):
                return finish("malformed_response")
            if item.get("type") == "reasoning":
                continue
            if item.get("type") != "message" or not isinstance(item.get("content"), list):
                return finish("unexpected_output")
            for part in item["content"]:
                if not isinstance(part, dict) or part.get("type") != "output_text" or not isinstance(part.get("text"), str):
                    return finish("unexpected_output")
                pieces.append(part["text"])
        text = "".join(pieces)
    else:
        choices = data.get("choices")
        if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
            return finish("malformed_response")
        choice = choices[0]
        if choice.get("finish_reason") == "length":
            return finish("output_limit")
        if choice.get("finish_reason") != "stop":
            return finish("incomplete")
        message = choice.get("message")
        if not isinstance(message, dict) or message.get("tool_calls"):
            return finish("unexpected_output")
        text = message.get("content")
    if not isinstance(text, str) or not text.strip():
        return finish("no_final_answer")
    return finish("complete", "none", text)
