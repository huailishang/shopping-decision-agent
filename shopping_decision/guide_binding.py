"""Local, restrictive lifecycle registry. It cannot approve a new source or revision."""
from pathlib import Path
import json

REGISTRY=Path(__file__).resolve().parents[1]/"knowledge/printer_cognition_guide_v1.json"
KNOWN=("hp-cn-home","brother-cn-202405-brochure","rtings-cost-method-2021")

def source_lifecycle():
    unknown={sid:{"revision":None,"status":"unavailable"} for sid in KNOWN}
    try:
        with REGISTRY.open("rb") as f:raw=f.read(16385)
        if len(raw)>16384: return unknown
        def unique(pairs):
            obj={}
            for k,v in pairs:
                if k in obj:raise ValueError("duplicate registry key")
                obj[k]=v
            return obj
        data=json.loads(raw.decode("utf8"),object_pairs_hook=unique)
        if not isinstance(data,dict) or set(data)!={"schema_version","sources"} or type(data["schema_version"]) is not int or data["schema_version"]!=1 or not isinstance(data["sources"],dict):return unknown
        for sid in KNOWN:
            row=data["sources"].get(sid)
            if not isinstance(row,dict) or set(row)!={"revision","status"} or type(row["revision"]) is not int or not 1<=row["revision"]<=1000000 or row["status"] not in ("active","withdrawn","pending_review"):continue
            state="withdrawn" if row["status"]=="withdrawn" else "active" if row["revision"]==1 and row["status"]=="active" else "pending_review"
            unknown[sid]={"revision":row["revision"],"status":state}
        return unknown
    except (OSError,ValueError,TypeError,RecursionError):
        return unknown
