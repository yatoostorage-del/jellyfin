import os, time, json, requests
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, unquote

BASE      = "https://yatoo.tualbola.workers.dev/0:/"
MEDIA     = Path("/media")
STATE     = MEDIA / ".state.json"
INTERVAL  = 300
VIDEO     = {".mkv", ".mp4", ".avi", ".mov", ".m4v", ".ts"}

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

def scan(path):
    found = {}
    for name, url, is_dir in ls(BASE + path):
        if is_dir:
            for n2, u2, d2 in ls(url):
                if d2:
                    for n3, u3, d3 in ls(u2):
                        if not d3 and Path(n3).suffix in VIDEO:
                            found[f"{path}{clean(name)}/{clean(n2)}/{clean(Path(n3).stem)}.strm"] = u3
                elif Path(n2).suffix in VIDEO:
                    found[f"{path}{clean(name)}/{clean(Path(n2).stem)}.strm"] = u2
        elif Path(name).suffix in VIDEO:
            found[f"{path}{clean(Path(name).stem)}.strm"] = url
    return found

def apply(remote, state):
    for k, v in remote.items():
        if state.get(k) != v:
            p = MEDIA / k
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(v + "\n")
            print("+", k)
    for k in list(state):
        if k not in remote:
            (MEDIA / k).unlink(missing_ok=True)
            print("-", k)

def run():
    MEDIA.mkdir(exist_ok=True)
    state = load()
    remote = {**scan("Movies/"), **scan("Series/")}
    apply(remote, state)
    save(remote)

while True:
    try: run()
    except Exception as e: print("err:", e)
    time.sleep(INTERVAL)
