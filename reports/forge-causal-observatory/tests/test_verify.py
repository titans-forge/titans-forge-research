"""Rehashed corruption controls test semantics, not just manifest matching."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('public_observatory_verifier', ROOT/'scripts/verify.py')
V = importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(V)


def dump(path, value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')


def rehash(root):
    manifest = V.read(root/'MANIFEST.json')
    for name in manifest['files']:
        data = (root/name).read_bytes()
        manifest['files'][name] = {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    dump(root/'MANIFEST.json',manifest)


class ReleaseEvidence(unittest.TestCase):
    def test_original_preserves_scientific_failures(self):
        result = V.verify(ROOT)
        self.assertEqual(result['evidence_integrity'],'PASS')
        self.assertEqual(result['agent_causal_passes'],0)
        self.assertEqual(result['cheap_causal_passes'],1)
        self.assertEqual(result['saved_logits_checked'],95634)
        self.assertEqual(result['inference_replays'],0)

    def test_all_three_seeds_reject_rehashed_semantic_corruption(self):
        for seed in V.SEEDS:
            for name in ('raw_logit','gate','duplicate','budget','retained','choice','donor','threshold','split'):
                with self.subTest(seed=seed,corruption=name),tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)/'package';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
                    path = root/f'evidence/seed_{seed}.json';trial = V.read(path)
                    if name == 'raw_logit':
                        row = trial['score']['rows'][0];pair = trial['split']['evaluation'][0]
                        truth = sum(pair)%11;pred = max(range(11),key=row['logits'][0].__getitem__)
                        changed = (truth+1)%11 if pred == truth else truth
                        row['logits'][0] = [999.0 if i == changed else 0.0 for i in range(11)]
                    elif name == 'gate':trial['score']['gates']['agent']['pass'] = True
                    elif name == 'duplicate':trial['score']['rows'][-1] = copy.deepcopy(trial['score']['rows'][0])
                    elif name == 'budget':trial['score']['budget']['calls'] = 34
                    elif name == 'retained':trial['score']['rows'][0]['retained_units'] = []
                    elif name == 'choice':trial['reply']['raw_answer'] = '{"choice":true}'
                    elif name == 'donor':
                        indexes = next(iter(trial['geometry']['evaluation_donors'].values()))
                        indexes[0] = (indexes[0]+1)%60
                    elif name == 'threshold':trial['config']['preservation_floor'] = .90
                    else:trial['split']['evaluation'][0] = trial['split']['discovery'][0]
                    dump(path,trial);rehash(root)
                    with self.assertRaises(ValueError):V.verify(root)

    def test_unmanifested_file_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'package';shutil.copytree(ROOT,root)
            (root/'unexpected.json').write_text('{}')
            with self.assertRaises(ValueError):V.verify(root)

    def test_modified_file_without_rehash_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'package';shutil.copytree(ROOT,root)
            (root/'RESULTS.md').write_text('Changed claim')
            with self.assertRaises(ValueError):V.verify(root)

    def test_manifest_escape_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'package';shutil.copytree(ROOT,root)
            manifest = V.read(root/'MANIFEST.json')
            manifest['files']['../outside'] = {'bytes':0,'sha256':'0'*64}
            dump(root/'MANIFEST.json',manifest)
            with self.assertRaises(ValueError):V.verify(root)

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'package';shutil.copytree(ROOT,root)
            path = root/'RESULTS.md';path.unlink();path.symlink_to(ROOT/'RESULTS.md')
            with self.assertRaises(ValueError):V.verify(root)

    def test_private_runtime_metadata_rejected_after_rehash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)/'package';shutil.copytree(ROOT,root)
            path = root/'evidence/seed_211.json';trial = V.read(path)
            trial['runtime_state'] = {'pid':1234}
            dump(path,trial);rehash(root)
            with self.assertRaises(ValueError):V.verify(root)

    def test_private_path_scan_rejects_actual_path(self):
        with self.assertRaises(ValueError):V.privacy('/'+'Users'+'/example/private-file')

    def test_duplicate_json_key_rejected(self):
        with self.assertRaises(ValueError):V.decode('{"choice":1,"choice":2}')

    def test_nonfinite_json_rejected(self):
        for literal in ('NaN','Infinity','-Infinity'):
            with self.subTest(literal=literal),self.assertRaises(ValueError):V.decode('{"x":'+literal+'}')


if __name__ == '__main__':unittest.main()
