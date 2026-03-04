import time, json, requests
from pathlib import Path
from urllib.parse import quote

BASE     = "https://app-9fc0f0fd-fcb7-4e8a-8357-ea455d9c28c1.cleverapps.io"   # e.g. https://app-xxxx.cleverapps.io
MEDIA    = Path("./media")
STATE    = MEDIA / ".state.json"
INTERVAL = 120
VIDEO    = {".mkv", ".mp4", ".avi", ".mov", ".m4v", ".ts"}

S = requests.Session()

def log(msg): print(msg, flush=True)

def api_list(path):
    r = S.post(f"{BASE}/api/fs/list", 
               json={"path": path, "password": "", "page": 1, "per_page": 0, "refresh": False},
               timeout=30)
    r.raise_for_status()
    return r.json()

def clean(name):
    for c in '<>:"/\\|?*': name = name.replace(c, "")
    return name.strip()

def load():
    return json.loads(STATE.read_text()) if STATE.exists() else {}

def save(s):
    STATE.write_text(json.dumps(s))

def scan(path, prefix):
    found = {}
    try:
        data = api_list(path)
    except Exception as e:
        log(f"  [ERR] {path}: {e}"); return found

    if data.get("code") != 200:
        log(f"  [ERR] {path}: {data.get('message')}"); return found

    files = data.get("data", {}).get("content") or []
    log(f"\n[{prefix}] {len(files)} items")

    for i, f in enumerate(files, 1):
        name   = f.get("name", "")
        is_dir = f.get("is_dir", False)
        log(f"  [{i}/{len(files)}] {'📁' if is_dir else '🎬'} {name}")
        if is_dir:
            found.update(scan(f"{path}/{name}", f"{prefix}/{clean(name)}"))
        elif Path(name).suffix.lower() in VIDEO:
            url = f"{BASE}/d{path}/{quote(name)}"
            key = f"{prefix}/{clean(Path(name).stem)}.strm"
            found[key] = url
            log(f"       → {url}")

    return found

def apply(remote, state):
    added = removed = updated = 0
    for k, v in remote.items():
        if k not in state:
            p = MEDIA / k; p.parent.mkdir(parents=True, exist_ok=True); p.write_text(v + "\n")
            log(f"  [+] {k}"); added += 1
        elif state[k] != v:
            (MEDIA / k).write_text(v + "\n")
            log(f"  [~] {k}"); updated += 1
    for k in state:
        if k not in remote:
            (MEDIA / k).unlink(missing_ok=True)
            log(f"  [-] {k}"); removed += 1
    log(f"\n  Summary → added:{added}  updated:{updated}  removed:{removed}")

def run():
    MEDIA.mkdir(exist_ok=True)
    log("=" * 50)
    log("Sync started")
    log("=" * 50)
    state  = load()
    remote = {**scan("/gdrive/Movies", "Movies"), **scan("/gdrive/Series", "Series")}
    log("\nApplying changes...")
    apply(remote, state)
    save(remote)
    log("\nSync complete. Sleeping 5 min...\n")

while True:
    try: run()
    except Exception as e: log(f"[ERR] {e}")
    time.sleep(INTERVAL)
