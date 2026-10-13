"""Offline publication checks; no network, model loading or controller actions."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
PACK=ROOT/'reports/sparse-activation-glm52'
manifest=json.loads((PACK/'PUBLICATION_SHA256.json').read_text())
actual={str(p.relative_to(PACK)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in PACK.rglob('*') if p.is_file() and p.name!='PUBLICATION_SHA256.json'}
assert actual==manifest, 'Publication file set or hash changed'
for name in actual:
    p=PACK/name
    if p.suffix not in ('.md','.json','.svg'):continue
    text=p.read_text()
    assert not re.search(r'/Users/|/home/|WFAPPR_|FMC_|SPINE_|Sovereign_Mesh|-----BEGIN .*PRIVATE KEY|sk-[A-Za-z0-9]{20,}',text),name
    if p.suffix=='.json':json.loads(text)
    if p.suffix=='.md':
        for link in re.findall(r'\]\(([^)]+)\)',text):
            if ':' in link or link.startswith('#'):continue
            assert (p.parent/link.split('#')[0]).exists(),(name,link)
subprocess.run([sys.executable,'-B',str(PACK/'verify_glm_5_2_colibri_m5max128_release.py')],check=True)
print('Publication checks passed:',len(actual),'files; historical evidence only.')
