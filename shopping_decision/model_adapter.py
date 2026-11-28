"""Offline model protocol contract. Transport is caller-injected; no retry or IO."""
from dataclasses import dataclass
import hashlib
import json

@dataclass(frozen=True)
class ModelRoute:
    provider: str
    model: str
    protocol: str
    context_window: int
    max_output: int
    capability_source: str
    reasoning_fields: tuple = ()
    fixture: bool = True

    def __post_init__(self):
        if not all(isinstance(x, str) and x.strip() for x in
                   (self.provider, self.model, self.capability_source)):
            raise ValueError("unknown_route")
        if self.protocol not in ("responses", "chat_completions"):
            raise ValueError("unsupported_protocol")
        if (type(self.context_window) is not int or type(self.max_output) is not int
                or not 0 < self.max_output < self.context_window or type(self.fixture) is not bool):
            raise ValueError("invalid_route_capacity")
        keys = [k for k,v in self.reasoning_fields]
        if len(keys) != len(set(keys)) or set(keys) - {"reasoning","reasoning_effort","enable_thinking","thinking"}:
            raise ValueError("unsupported_reasoning_fields")

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)

def payload(route, system, packet, output_cap, reasoning_reserve=0):
    if not isinstance(route, ModelRoute):
        raise ValueError("unknown_route")
    if (type(output_cap) is not int or output_cap <= 0 or type(reasoning_reserve) is not int
            or reasoning_reserve < 0 or output_cap + reasoning_reserve > route.max_output):
        raise ValueError("invalid_output_budget")
    fields = dict(route.reasoning_fields)
    if route.protocol == "responses":
        return {"model":route.model,"instructions":system,"input":canonical(packet),
                "max_output_tokens":output_cap+reasoning_reserve,"stream":False,**fields}
    return {"model":route.model,"messages":[{"role":"system","content":system},
            {"role":"user","content":canonical(packet)}],"max_tokens":output_cap+reasoning_reserve,
            "stream":False,**fields}

def normalize(route, *, http_status=None, raw=None, transport_error=None,
              request_id=None, context_id=None, elapsed_ms=None):
    """Normalize a single non-streaming attempt, keeping identity separate from completion."""
    if not isinstance(route,ModelRoute):
        raise ValueError("unknown_route")
    result = {"provider":route.provider,"declared_model":route.model,"observed_model":None,
              "identity":"unknown","protocol":route.protocol,"request_id":request_id,
              "context_id":context_id,"http_status":http_status,"usage":None,"provider_code":None,
              "finish_reason":None,"elapsed_ms":elapsed_ms,"raw_sha256":None,
              "status":None,"text":None,"business_accepted":False,"fixture":route.fixture}
    def finish(status,text=None):
        return dict(result,status=status,text=text, text_sha256=hashlib.sha256(text.encode("utf8")).hexdigest() if isinstance(text,str) else None)
    if raw is not None:
        if not isinstance(raw,(str,bytes)):
            return finish("malformed_response")
        raw_bytes = raw.encode("utf8") if isinstance(raw,str) else raw
        result["raw_sha256"] = hashlib.sha256(raw_bytes).hexdigest()
    else:
        raw_bytes = None
    if transport_error:
        return finish("timeout" if transport_error=="timeout" else "transport_unknown")
    if raw_bytes is not None and len(raw_bytes)>1048576:
        return finish("response_over_limit")
    try:
        data=json.loads(raw_bytes) if raw_bytes is not None else None
    except (ValueError,UnicodeError,RecursionError):
        data=None
    if isinstance(data,dict):
        error=data.get("error")
        result["provider_code"]=(error.get("code") if isinstance(error,dict) else None) or data.get("code")
        result["usage"]=data.get("usage") if isinstance(data.get("usage"),dict) else None
        observed=data.get("model")
        if isinstance(observed,str) and observed.strip():
            result["observed_model"]=observed
            result["identity"]="matched" if observed==route.model else "mismatch"
    if http_status in (401,403):
        return finish("auth_or_permission")
    if http_status==429:
        return finish("rate_or_quota_limit")
    if http_status==400:
        return finish("context_limit" if result["provider_code"] in
                      ("context_length_exceeded","max_context_length_exceeded") else "invalid_request")
    if type(http_status) is int and http_status>=500:
        return finish("provider_error")
    if http_status!=200:
        return finish("unexpected_http_status")
    if not isinstance(data,dict):
        return finish("malformed_response")
    if data.get("success") is False or data.get("error"):
        return finish("application_error")
    if result["identity"]=="mismatch":
        return finish("model_mismatch")
    def unsupported(obj):
        return any(key in obj and obj[key] not in (None, [], "") for key in ("tool_calls","function_call","refusal"))
    def nested_unsupported(obj):
        stack = [obj]
        while stack:
            part = stack.pop()
            if isinstance(part, dict):
                if unsupported(part) or part.get("type") in (
                    "function_call", "tool_call", "tool_calls", "refusal",
                    "custom_tool_call", "computer_call", "web_search_call", "file_search_call"):
                    return True
                stack.extend(part.values())
            elif isinstance(part, list):
                stack.extend(part)
        return False

    def valid_reasoning(item):
        if nested_unsupported(item):
            return False
        for key, allowed in (("summary", {"summary_text"}), ("content", {"reasoning_text", "summary_text"})):
            if key in item and item[key] is not None:
                parts = item[key]
                if not isinstance(parts, list) or len(parts) > 64:
                    return False
                if any(not isinstance(part, dict) or not isinstance(part.get("type"),str) or part.get("type") not in allowed
                       or not isinstance(part.get("text"), str) for part in parts):
                    return False
        return True

    if unsupported(data):
        return finish("unexpected_output")
    if route.protocol=="responses":
        result["finish_reason"]=data.get("status")
        if data.get("status")=="incomplete":
            details=data.get("incomplete_details")
            reason=details.get("reason") if isinstance(details,dict) else None
            result["finish_reason"]=reason
            return finish("output_limit" if reason=="max_output_tokens" else "incomplete")
        if data.get("status")!="completed" or not isinstance(data.get("output"),list):
            return finish("incomplete")
        if len(data["output"])>64:
            return finish("response_over_limit")
        messages=[]
        reasoning=False
        for item in data["output"]:
            if not isinstance(item,dict):
                return finish("malformed_response")
            if unsupported(item):
                return finish("unexpected_output")
            if item.get("type")=="reasoning":
                if not valid_reasoning(item):
                    return finish("unexpected_output")
                reasoning=True
                continue
            if item.get("type")!="message" or item.get("role")!="assistant":
                return finish("unexpected_output")
            if item.get("status") not in (None,"completed") or not isinstance(item.get("content"),list):
                return finish("incomplete")
            if len(item["content"])>64:
                return finish("response_over_limit")
            parts=[]
            for part in item["content"]:
                if not isinstance(part,dict) or unsupported(part) or part.get("type")!="output_text" or not isinstance(part.get("text"),str):
                    return finish("unexpected_output")
                parts.append(part["text"])
            messages.append("".join(parts))
        if len(messages)>1:
            return finish("unexpected_output")
        if not messages and reasoning:
            return finish("reasoning_only")
        text=messages[0] if messages else None
    else:
        choices=data.get("choices")
        if not isinstance(choices,list) or len(choices)!=1 or not isinstance(choices[0],dict):
            return finish("malformed_response")
        choice=choices[0]
        if unsupported(choice):
            return finish("unexpected_output")
        result["finish_reason"]=choice.get("finish_reason")
        if choice.get("finish_reason")=="length":
            return finish("output_limit")
        if choice.get("finish_reason")!="stop":
            return finish("incomplete")
        message=choice.get("message")
        if not isinstance(message,dict) or message.get("role")!="assistant" or unsupported(message):
            return finish("unexpected_output")
        if nested_unsupported(message) or ("reasoning_content" in message and message["reasoning_content"] is not None and not isinstance(message["reasoning_content"],str)):
            return finish("unexpected_output")
        text=message.get("content")
        if not text and message.get("reasoning_content"):
            return finish("reasoning_only")
    if not isinstance(text,str) or not text.strip():
        return finish("no_final_answer")
    return finish("complete" if result["identity"]=="matched" else "identity_unknown",text)
