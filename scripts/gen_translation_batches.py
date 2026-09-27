"""Generate translation batches for ko translation agents.
Outputs .translation/batches.json and glossary part files.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUDGET = 130_000

SKIP_DIRS = {".git", "i18n", ".github", "node_modules"}
SKIP_FILES = {  # repo meta / already translated, relative to ROOT
    "README.md", "CHANGELOG.md", "BACKERS.md", "SPONSORS.md",
    "CODE_OF_CONDUCT.md", "FORKING.md", "TRANSLATION_GUIDE.ko.md",
    "glossary/terms.md",  # handled via part split below
}

def target_for(src: str) -> str:
    d, b = os.path.split(src)
    if b == "en.md":
        return os.path.join(d, "ko.md")
    if b.endswith(".md"):
        return os.path.join(d, b[:-3] + ".ko.md")
    raise ValueError(src)

# ---- collect groups -------------------------------------------------------
groups = {}  # container -> list of src
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
    for fn in filenames:
        if not fn.endswith(".md"):
            continue
        rel = os.path.relpath(os.path.join(dirpath, fn), ROOT).replace("\\", "/")
        if rel in SKIP_FILES:
            continue
        parts = rel.split("/")
        if parts[0] in ("phases", "certifications") and len(parts) >= 2:
            if fn == "en.md" and parts[-2] == "docs":
                container = "/".join(parts[:-2])          # lesson dir
            elif "lessons/" in rel and "/docs/" in "/" + rel:
                container = "/".join(parts[:-2])
            else:
                # loose file inside area: attach to nearest lesson dir if under one,
                # else to the phase/track dir itself
                container = os.path.dirname(rel)
                while container.count("/") > (2 if parts[0] == "phases" else 2):
                    container = container.rsplit("/", 1)[0]
        else:
            container = parts[0] if len(parts) > 1 else "<root>"
        groups.setdefault(container, []).append(rel)

# merge tiny loose containers into their top area
merged = {}
for c, files in groups.items():
    if c == "<root>" or c.count("/") == 0:
        merged.setdefault(c, []).extend(files)
    elif c.count("/") == 1 and c.split("/")[0] in ("skills", "glossary", "book", "docs", "site"):
        merged.setdefault(c.split("/")[0], []).extend(files)
    else:
        merged[c] = files
# root files like ROADMAP.md land in <root>
for c in list(merged):
    if c == "<root>":
        merged["<root>"] = merged.pop("<root>")

def area_of(container: str) -> str:
    return "<root>" if container == "<root>" else container.split("/")[0]

# ---- pack batches (never cross area boundary) ------------------------------
def size_of(rel):
    return os.path.getsize(os.path.join(ROOT, rel))

order = sorted(merged.items(), key=lambda kv: kv[0])
batches = []
cur, cur_size, cur_area = [], 0, None
for container, files in order:
    files = sorted(files)
    a = area_of(container)
    csz = sum(size_of(f) for f in files)
    if cur and (a != cur_area or cur_size + csz > BUDGET):
        batches.append(cur); cur, cur_size = [], 0
    cur_area = a
    cur.extend((f, target_for(f)) for f in files)
    cur_size += csz
    if cur_size >= BUDGET:
        batches.append(cur); cur, cur_size = [], 0
if cur:
    batches.append(cur)

os.makedirs(os.path.join(ROOT, ".translation"), exist_ok=True)
manifest = []
for i, b in enumerate(batches):
    total = sum(size_of(f) for f, _ in b)
    manifest.append({
        "id": f"b{i:03d}",
        "bytes": total,
        "files": [{"src": s, "dst": t} for s, t in b],
    })

with open(os.path.join(ROOT, ".translation", "batches.json"), "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=1)

print(f"{len(manifest)} batches, {sum(m['bytes'] for m in manifest)/1e6:.1f} MB")
for m in manifest[:5]:
    print(m["id"], m["bytes"], len(m["files"]), "files, e.g.", m["files"][0]["src"])

# ---- glossary terms.md split ----------------------------------------------
terms = open(os.path.join(ROOT, "glossary/terms.md"), encoding="utf-8").read()
lines = terms.splitlines(keepends=True)
# find heading line indexes for '^## X'
idx = [i for i, l in enumerate(lines) if re.match(r"^## ", l)]
# preface = everything before first heading
chunks = []
if idx and idx[0] > 0:
    chunks.append("".join(lines[:idx[0]]))
bounds = idx + [len(lines)]
# ~6 letters per part
per = 6
for ci in range(0, len(bounds) - 1, per):
    end = min(bounds[-1], bounds[min(ci + per, len(bounds) - 1)])
    start = bounds[ci]
    chunks.append("".join(lines[start:end]))
for ci, ch in enumerate(chunks):
    p = os.path.join(ROOT, ".translation", f"terms.ko.part{ci:02d}.src.md")
    open(p, "w", encoding="utf-8", newline="\n").write(ch)
    print("part", ci, len(ch))
