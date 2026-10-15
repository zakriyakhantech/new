#!/usr/bin/env python3
"""Conservative NameVerse JSON audit. Defaults to report-only mode."""
import argparse, json
from pathlib import Path

LOW = {"low", "unknown", "unverified", "not_established", "none", ""}

def urls(data):
    out=[]
    src=data.get("evidence",{}).get("sources",[])
    for x in src if isinstance(src,list) else []:
        if isinstance(x,str) and x.strip().startswith(("https://","http://")): out.append(x.strip())
        elif isinstance(x,dict):
            for k in ("url","uri","source_url","href"):
                v=x.get(k)
                if isinstance(v,str) and v.startswith(("https://","http://")): out.append(v)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",default="upgrading/names_upgraded")
    ap.add_argument("--apply",action="store_true",help="only correct conservative verification flags")
    args=ap.parse_args(); root=Path(args.root)
    if not root.exists(): raise SystemExit(f"Missing directory: {root}")
    total=flagged=changed=invalid=0
    for p in root.rglob("*.json"):
        if any(x in {".git","node_modules","dist","build"} for x in p.parts): continue
        try: obj=json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"INVALID_JSON {p}: {e}"); invalid+=1; continue
        total+=1; d=obj.get("data",{}); issues=[]; updates=[]
        if not isinstance(d,dict):
            print(f"INVALID_SCHEMA {p}: data object missing"); flagged+=1; continue
        mc=str(d.get("core_meaning",{}).get("meaning_confidence","")).lower()
        ec=str(d.get("etymology",{}).get("etymology_confidence","")).lower()
        oc=str(d.get("origin",{}).get("origin_confidence","")).lower()
        has_source=bool(urls(d))
        v=d.get("verification",{}); ed=d.get("editorial",{})
        if v.get("tier1_verified") is True and (mc in LOW or oc in LOW or not has_source):
            issues.append("tier1 contradicts confidence/evidence")
            updates.append((v,"tier1_verified",False))
        if ed.get("needs_manual_verification") is False and (mc in LOW or ec in LOW or oc in LOW or not has_source):
            issues.append("manual review incorrectly disabled")
            updates.append((ed,"needs_manual_verification",True))
        if not has_source: issues.append("no traceable source URL")
        faq=d.get("faq",[])
        if isinstance(faq,list):
            qs=[" ".join(str(x.get("question",x.get("q",""))).casefold().split()) for x in faq if isinstance(x,dict)]
            if len(qs)!=len(set(qs)): issues.append("duplicate FAQ questions")
        if issues:
            flagged+=1; print(f"REVIEW {p}: " + "; ".join(issues))
        if args.apply and updates:
            for target,key,val in updates: target[key]=val
            p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); changed+=1
    print(f"SUMMARY checked={total} flagged={flagged} changed={changed} invalid_json={invalid}")
    print("This audit does not prove meanings/translations true; source and linguistic review remain necessary.")
if __name__=="__main__": main()
