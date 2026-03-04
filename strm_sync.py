import time, json, requests
from pathlib import Path

BASE     = "https://yatoo.tualbola.workers.dev"
MEDIA    = Path("/media")
STATE    = MEDIA / ".state.json"
INTERVAL = 300
VIDEO    = {".mkv", ".mp4", ".avi", ".mov", ".m4v", ".ts"}

S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0"})

def log(msg): print(msg, flush=True)

def api_list(path, page_token=""):
    """BhadooGDIndex API - POST ?a=list"""
    url = f"{BASE}/{path}?a=list"
    r = S.post(url, data={"page_token": page_token, "page_index": 0}, timeout=30)
    r.raise_for_status()
    return r.json()

def clean(name):
    for c in '<>:"/\\|?*': name = name.replace(c, "")
    return name.strip()

def scan(path, out_prefix):
    found = {}
    try:
        data = api_list(path)
    except Exception as e:
        log(f"  [ERR] {path}: {e}")
        return found

    files = data.get("data", {}).get("files", [])
    log(f"\n[{out_prefix}] {len(files)} items")

    for i, f in enumerate(files, 1):
        name = f.get("name", "")
        is_dir = f.get("mimeType", "") == "application/vnd.google-apps.folder"
        log(f"  [{i}/{len(files)}] {name}")

        if is_dir:
            sub = scan(f"{path}/{name}", f"{out_prefix}/{clean(name)}")
            found.update(sub)
        elif Path(name).suffix.lower() in VIDEO:
            url = f"{BASE}/{path}/{name}?a=view"
            key = f"{out_prefix}/{clean(Path(name).stem)}.strm"
            found[key] = url
            log(f"       → {url}")

    return found

def load():
    return json.loads(STATE.read_text()) if STATE.exists() else {}

def save(s):
    STATE.write_text(json.dumps(s))

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
    log("Sync started")
    log("=" * 50)
    state  = load()
    remote = {}
    remote.update(scan("0:/Movies", "Movies"))
    remote.update(scan("0:/Series", "Series"))
    log("\nApplying changes...")
    apply(remote, state)
    save(remote)
    log("\nSync complete. Sleeping 5 min...\n")

while True:
    try: run()
    except Exception as e: log(f"[ERR] {e}")
    time.sleep(INTERVAL)
