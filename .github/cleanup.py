"""Delete expired drops and orphaned chunks. Run by .github/workflows/cleanup.yml."""
import json, os, sys, time, pathlib

now_ms = int(time.time() * 1000)
root = pathlib.Path('.')
removed = 0
keep = set()

for f in sorted(root.glob('d/*.json')):
    try:
        drop = json.loads(f.read_text())
    except Exception:
        drop = {}
    blobs = [b for b in drop.get('blobs', []) if isinstance(b, str) and b.startswith('b/')]
    if drop.get('expiresAt', 0) < now_ms:
        for b in blobs:
            p = root / b
            if p.exists():
                p.unlink(); removed += 1
        f.unlink(); removed += 1
    else:
        keep.update(blobs)

# Chunks no drop points at (a send that failed half-way), older than 3 hours.
for p in root.glob('b/*.bin'):
    rel = 'b/' + p.name
    if rel in keep:
        continue
    try:
        ts = int(p.name.split('-', 1)[0])
    except ValueError:
        ts = 0
    if now_ms - ts > 3 * 3600 * 1000:
        p.unlink(); removed += 1

print(f'removed {removed} files')
with open(os.environ.get('GITHUB_OUTPUT', os.devnull), 'a') as out:
    out.write(f'removed={removed}\n')
