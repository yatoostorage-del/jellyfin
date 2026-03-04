import time, json, requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote

BASE     = "https://yatoo.tualbola.workers.dev/0:/"
MEDIA    = Path("/media")
STATE    = MEDIA / ".state.json"
INTERVAL = 300
VIDEO    = {".mkv", ".mp4", ".avi", ".mov", ".m4v", ".ts"}

def get(url):
    return BeautifulSoup(requests.get(url, timeout=30).text, "html.parser")

def ls(url):
    out = []
    for a in get(url).find_all("a", href=True):
        h = a["href"]
        if h in ("#", "/", "../", "") or h.startswith("?"): continue
        full = h if h.startswith("http") else urljoin(url, h)
        out.append((unquote(h.rstrip("/").split("/")[-1]), full, h.endswith("/")))
    return out

def clean(name):
    for c in '<>:"/\\|?*': name = name.replace(c, "")
    return name.strip()

def load():
    return json.loads(STATE.read_text()) if STATE.exists() else {}

def save(s):
    STATE.write_text(json.dumps(s))

def log(msg): print(msg, flush=True)

def scan(path, label):
    found = {}
    entries = ls(BASE + path)
    total = len(entries)
    log(f"\n[{label}] Found {total} items — scanning...")
    for i, (name, url, is_dir) in enumerate(entries, 1):
        log(f"  [{i}/{total}] {name}")
        if is_dir:
            for n2, u2, d2 in ls(url):
                if d2:
                    for n3, u3, d3 in ls(u2):
                        if not d3 and Path(n3).suffix in VIDEO:
                            k = f"{path}{clean(name)}/{clean(n2)}/{clean(Path(n3).stem)}.strm"
                            found[k] = u3
                            log(f"       → {u3}")
                elif Path(n2).suffix in VIDEO:
                    k = f"{path}{clean(name)}/{clean(Path(n2).stem)}.strm"
                    found[k] = u2
                    log(f"       → {u2}")
        elif Path(name).suffix in VIDEO:
            k = f"{path}{clean(Path(name).stem)}.strm"
            found[k] = url
            log(f"       → {url}")
    log(f"[{label}] Done — {len(found)} strm URLs collected.")
    return found

def apply(remote, state):
    added = removed = updated = 0
    for k, v in remote.items():
        if k not in state:
            p = MEDIA / k; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(v + "\n")
            log(f"  [+] {k}")
            added += 1
        elif state[k] != v:
            (MEDIA / k).write_text(v + "\n")
            log(f"  [~] {k}")
            updated += 1
    for k in state:
        if k not in remote:
            (MEDIA / k).unlink(missing_ok=True)
            log(f"  [-] {k}")
            removed += 1
    log(f"\n  Summary → added:{added}  updated:{updated}  removed:{removed}")

def run():
    MEDIA.mkdir(exist_ok=True)
    log("=" * 50)
    log(f"Sync started")
    log("=" * 50)
    state  = load()
    remote = {**scan("Movies/", "Movies"), **scan("Series/", "Series")}
    log("\nApplying changes...")
    apply(remote, state)
    save(remote)
    log("\nSync complete. Sleeping 5 min...\n")

while True:
    try: run()
    except Exception as e: log(f"[ERR] {e}")
    time.sleep(INTERVAL)
