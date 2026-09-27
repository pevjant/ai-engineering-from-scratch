"""Verify translated ko files for given batch ids: exists, Hangul, size ratio, banner.
Usage: python scripts/verify_translation.py b000 b001 ...
No args = all batches. Exit 1 on failures.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ms = json.load(open(os.path.join(ROOT, ".translation", "batches.json"), encoding="utf-8"))
want = set(sys.argv[1:]) or {m["id"] for m in ms}
fails = []
ok = tot = 0
for m in ms:
    if m["id"] not in want:
        continue
    if m.get("glossary_part"):
        part = m["glossary_part"]
        dst = os.path.join(ROOT, ".translation", part.replace(".src.md", ".ko.md"))
        srcsz = m["bytes"]
        if not os.path.exists(dst):
            fails.append(f"{m['id']}: MISSING {part} -> ko")
        else:
            d = open(dst, encoding="utf-8").read()
            hang = len(re.findall(r"[\uac00-\ud7a3]", d)) / max(len(d), 1)
            if len(d) < srcsz * 0.4 or hang < 0.05:
                fails.append(f"{m['id']}: THIN {part} len={len(d)} src={srcsz} hang={hang:.2f}")
        continue
    for f in m["files"]:
        tot += 1
        dst = os.path.join(ROOT, f["dst"])
        srcsz = os.path.getsize(os.path.join(ROOT, f["src"]))
        if not os.path.exists(dst):
            fails.append(f"{m['id']}: MISSING {f['dst']}")
            continue
        d = open(dst, encoding="utf-8").read()
        hang = len(re.findall(r"[\uac00-\ud7a3]", d)) / max(len(d), 1)
        if hang < 0.03:
            fails.append(f"{m['id']}: NO-HANGUL {f['dst']} hang={hang:.3f}")
        elif len(d) < srcsz * 0.35:
            fails.append(f"{m['id']}: THIN {f['dst']} {len(d)} < {srcsz}*0.35")
        elif "🇰🇷" not in d[:800]:
            fails.append(f"{m['id']}: NO-BANNER {f['dst']}")
        else:
            ok += 1
print(f"OK {ok}/{tot} files; {len(fails)} failures")
for x in fails[:60]:
    print(" ", x)
sys.exit(1 if fails else 0)
