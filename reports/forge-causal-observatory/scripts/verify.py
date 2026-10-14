"""Validate saved synthetic evidence; no model/runtime/network dependency."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import random
import re
import sys

SEEDS = (211, 223, 227)
METHODS = ('zero', 'mean', 'resample')
SELECTORS = ('agent', 'cheap')
THRESHOLDS = {'quality_floor':0.99, 'preservation_floor':0.95,
              'complement_damage_floor':0.25}
MAX_FILE_BYTES = 4_000_000
SOURCE_ROLES = {'config','discovery_packet','discovery_results','discovery_catalog',
                'trained_fixture','fixture_manifest','proposal','answer','model_request',
                'model_response','proposal_receipt','call_receipt','selection','paired_results'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def fields(value, keys, label):
    require(type(value) is dict and set(value) == set(keys), label + ' fields')


def integer(value, low, high, label):
    require(type(value) is int and low <= value <= high, label)


def hash_string(value):
    require(type(value) is str and re.fullmatch('[0-9a-f]{64}', value), 'SHA-256 format')


def object_pairs(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, 'duplicate JSON key')
        value[key] = item
    return value


def decode(raw):
    def nonfinite(_):
        raise ValueError('nonfinite JSON literal')
    return json.loads(raw, object_pairs_hook=object_pairs, parse_constant=nonfinite)


def read(path):
    require(path.is_file() and not path.is_symlink(), 'regular file required')
    require(path.stat().st_size <= MAX_FILE_BYTES, 'file byte ceiling')
    return decode(path.read_text(encoding='utf-8'))


def digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def inventory(root):
    result = set()
    for folder, dirs, files in os.walk(root, followlinks=False):
        parent = Path(folder)
        for name in dirs[:]:
            require(not (parent / name).is_symlink(), 'symlink directory')
            if parent == root and name == '.git':
                dirs.remove(name)
        for name in files:
            path = parent / name
            require(not path.is_symlink(), 'symlink file')
            if parent == root and name == '.git':
                continue
            require(path.is_file(), 'nonregular inventory entry')
            result.add(path.relative_to(root).as_posix())
            require(len(result) <= 64, 'inventory file ceiling')
    return result


def privacy(text):
    # Assemble patterns so the checker does not flag its own source literals.
    forbidden = [r'/(?:Use' + r'rs|home|private|Volumes)/[^\s"<>]+',
                 r'[A-Za-z]:\\(?:Use' + r'rs|Windows)\\',
                 r'127\.' + r'0\.0\.1|localhost:\d+',
                 'BEGIN ' + '(?:RSA |EC |OPENSSH )?PRIVATE KEY',
                 r'\b(?:ghp_' + r'|github_pat_|sk-proj-)[A-Za-z0-9_\-]{12,}',
                 'titans_' + 'forge_kernel', 'Sovereign_' + 'Mesh',
                 r'WFAP' + r'PR_[A-Za-z0-9_]+' ]
    require(not any(re.search(pattern, text) for pattern in forbidden), 'privacy pattern found')


def verify_manifest(root):
    manifest = read(root / 'MANIFEST.json')
    fields(manifest, ('schema','version','scope','files'), 'manifest')
    require(manifest['schema'] == 'forge_observatory_public_manifest_v1' and
            manifest['version'] == '0.1.0' and
            manifest['scope'] == 'saved_evidence_verification', 'manifest identity')
    require(type(manifest['files']) is dict and 1 <= len(manifest['files']) < 64, 'manifest files')
    require('MANIFEST.json' not in manifest['files'], 'self-referential manifest')
    total = 0
    for name, expected in manifest['files'].items():
        path = PurePosixPath(name)
        require(type(name) is str and not path.is_absolute() and '..' not in path.parts and
                '\\' not in name and name == path.as_posix(), 'manifest path confinement')
        fields(expected, ('bytes','sha256'), 'file binding')
        integer(expected['bytes'], 0, MAX_FILE_BYTES, 'file size');hash_string(expected['sha256'])
        file = root / name
        require(file.is_file() and not file.is_symlink() and file.stat().st_size == expected['bytes'], 'file size/type mismatch')
        raw = file.read_bytes();total += len(raw)
        require(total <= 20_000_000, 'total byte ceiling')
        require(hashlib.sha256(raw).hexdigest() == expected['sha256'], 'file hash mismatch: ' + name)
        privacy(raw.decode('utf-8'))
    require(inventory(root) == set(manifest['files']) | {'MANIFEST.json'}, 'unmanifested or missing file')
    return len(manifest['files']) + 1


def validate_units(units):
    require(type(units) is list and len(units) == 16, 'unit coverage')
    ids = set()
    for unit in units:
        fields(unit, ('id','kind','weight_norm'), 'unit')
        uid = unit['id']
        require(type(uid) is str and re.fullmatch('U_[0-9a-f]{12}', uid) and uid not in ids, 'unit identity')
        require(unit['kind'] in ('attention_head','mlp_block'), 'unit kind')
        require(type(unit['weight_norm']) in (int,float) and math.isfinite(unit['weight_norm']) and unit['weight_norm'] >= 0, 'unit norm')
        ids.add(uid)
    require({u['kind'] for u in units} == {'attention_head','mlp_block'}, 'unit kinds')
    return ids


def common_masks(units, seed):
    rank = sorted(units, key=lambda x:(x['weight_norm'], x['id']))
    omitted = [rank[0]['id']]
    for kind in ('attention_head','mlp_block'):
        uid = next(x['id'] for x in rank if x['kind'] == kind)
        if uid not in omitted:
            omitted.append(uid)
    shuffled = sorted(x['id'] for x in units);random.Random(seed).shuffle(shuffled)
    for uid in shuffled:
        if len(omitted) == 8:
            break
        if uid not in omitted:
            omitted.append(uid)
    ids = {x['id'] for x in units}
    return [sorted(ids - {uid}) for uid in omitted]


def validate_mask(nodes, ids):
    require(type(nodes) is list and len(nodes) == len(set(nodes)) == 15 and
            nodes == sorted(nodes) and set(nodes) <= ids, 'mask identity')


def measure(row, examples):
    require(row['trace'] is True, 'reported trace assertion')
    scores = row['logits']
    require(type(scores) is list and len(scores) == len(examples), 'logit coverage')
    correct = 0
    for pair, values in zip(examples, scores):
        require(type(values) is list and len(values) == 11 and
                all(type(x) in (int,float) and math.isfinite(x) for x in values), 'finite logits')
        correct += max(range(11), key=values.__getitem__) == sum(pair) % 11
    integer(row['correct'],0,len(examples),'correct count')
    integer(row['agreement'],0,len(examples),'agreement count')
    require(row['correct'] == row['agreement'] == correct, 'saved outcome count')
    return correct


def validate_budget(value, calls, examples):
    fields(value, ('calls','max_calls','sequence_examples','batch_sizes'), 'budget')
    require(type(value['batch_sizes']) is list and len(value['batch_sizes']) == calls, 'batch coverage')
    for n in value['batch_sizes']:
        integer(n,0,121,'batch size')
    require(type(value['calls']) is int and value['calls'] == calls and
            type(value['max_calls']) is int and value['max_calls'] == 48 and
            type(value['sequence_examples']) is int and
            value['sequence_examples'] == sum(value['batch_sizes']) == examples, 'budget accounting')


def paired_gate(keep, comp):
    acc = min(r['correct'] / 61 for r in keep.values())
    agree = min(r['agreement'] / 61 for r in keep.values())
    damage = min((61 - r['correct']) / 61 for r in comp.values())
    return {'worst_keep_accuracy':acc, 'worst_keep_agreement':agree,
            'least_complement_damage':damage, 'preservation':min(acc,agree) >= .95,
            'complement_damage':damage >= .25,
            'pass':min(acc,agree) >= .95 and damage >= .25}


def verify_seed(trial, seed):
    fields(trial, ('schema','seed','config','packet','split','geometry','fixture','checkpoint_sha256',
        'versions','proposer_model','proposal','request','reply','selection','discovery','score','source_artifacts'), 'trial')
    require(trial['schema'] == 'forge_observatory_public_seed_v1' and type(trial['seed']) is int and trial['seed'] == seed, 'trial identity')
    cfg = trial['config']
    fields(cfg, ('seed','training_steps','learning_rate','split_salt','mask_size','common_masks','methods',
        'discovery_count','evaluation_count','quality_floor','preservation_floor','complement_damage_floor',
        'max_agent_output_tokens','max_agent_seconds'), 'config')
    require(cfg['seed'] == seed and cfg['training_steps'] == 1200 and cfg['learning_rate'] == .01 and
        cfg['mask_size'] == 15 and cfg['common_masks'] == 8 and cfg['methods'] == list(METHODS) and
        cfg['discovery_count'] == 60 and cfg['evaluation_count'] == 61 and
        cfg['max_agent_output_tokens'] == 64 and cfg['max_agent_seconds'] == 120 and
        {k:cfg[k] for k in THRESHOLDS} == THRESHOLDS and
        cfg['split_salt'] == f'robust-joint17-seed{seed}-2026-10-12', 'frozen config')
    ordered = [[a,b] for a in range(11) for b in range(11)]
    ordered.sort(key=lambda pair:hashlib.sha256((cfg['split_salt'] + ':' +
        json.dumps(pair,separators=(',',':'))).encode()).hexdigest())
    require(trial['split'] == {'discovery':ordered[:60],'evaluation':ordered[60:]}, 'exact split')
    discovery, evaluation = ordered[:60], ordered[60:]
    fixture = trial['fixture']
    fields(fixture, ('seed','steps','optimizer_steps','training_accuracy','quality','initial_parameter_hash','final_parameter_hash'), 'fixture')
    require(fixture['seed'] == seed and fixture['steps'] == fixture['optimizer_steps'] == 1200 and fixture['training_accuracy'] == 1.0, 'fixture quality')
    for key in ('initial_parameter_hash','final_parameter_hash'):
        hash_string(fixture[key])
    require(fixture['initial_parameter_hash'] != fixture['final_parameter_hash'], 'unchanged parameters')
    quality = fixture['quality'];fields(quality, ('accuracy','count','per_example'), 'training quality')
    require(quality['count'] == 121 and quality['accuracy'] == 1.0 and len(quality['per_example']) == 121, 'training coverage')
    seen = set()
    for row in quality['per_example']:
        fields(row, ('operands','expected','predicted','correct'), 'training outcome')
        pair = row['operands']
        require(type(pair) is list and len(pair) == 2, 'operands')
        for n in pair:
            integer(n,0,10,'operand')
        require(tuple(pair) not in seen and row['correct'] is True and
                row['expected'] == row['predicted'] == sum(pair) % 11, 'training outcome')
        integer(row['expected'],0,10,'training expected');integer(row['predicted'],0,10,'training predicted')
        seen.add(tuple(pair))
    hash_string(trial['checkpoint_sha256'])
    require(type(trial['versions']) is dict and set(trial['versions']) == {'dm-haiku','jax','jaxlib','numpy','tracr'} and
            all(type(v) is str and len(v) < 32 for v in trial['versions'].values()), 'version metadata')
    packet = trial['packet']
    fields(packet, ('schema','seed','model_id','checkpoint_sha256','task','training_domain_only','mask_size',
        'discovery_count','evaluation_count','methods','units','observations','rule'), 'packet')
    require(packet['schema'] == 'forge_robust_joint17_packet_v1' and packet['seed'] == seed and
        packet['model_id'] == f'fine{seed}_' + trial['checkpoint_sha256'][:16] and
        packet['checkpoint_sha256'] == trial['checkpoint_sha256'] and packet['task'] == '(a+b)%11' and
        packet['training_domain_only'] is True and packet['mask_size'] == 15 and
        packet['discovery_count'] == 60 and packet['evaluation_count'] == 61 and
        packet['methods'] == list(METHODS) and
        packet['rule'] == 'Choose any 15-unit mask. Measured masks may be reused by either selector.', 'packet identity')
    ids = validate_units(packet['units']);common = common_masks(packet['units'],seed)
    observations = packet['observations']
    require(type(observations) is list and len(observations) == 8, 'observations')
    for i, row in enumerate(observations):
        fields(row, ('mask','nodes','correct','agreement'), 'observation')
        require(row['mask'] == f'common_{i+1}' and row['nodes'] == common[i], 'common mask')
        for metric in ('correct','agreement'):
            fields(row[metric], METHODS, 'observation methods')
            for count in row[metric].values():integer(count,0,60,'observation count')
    geom = trial['geometry'];fields(geom, ('parent_by_unit','discovery_donors','evaluation_donors'), 'geometry')
    require(set(geom['parent_by_unit']) == ids, 'parent coverage')
    for uid in geom['parent_by_unit'].values():
        require(type(uid) is str and re.fullmatch('U_[0-9a-f]{12}',uid), 'parent opaque ID')
    for key, cases in (('discovery_donors',discovery),('evaluation_donors',evaluation)):
        require(set(geom[key]) == ids, 'donor coverage')
        for uid, indexes in geom[key].items():
            expected = [int(hashlib.sha256((cfg['split_salt'] + ':' + geom['parent_by_unit'][uid] + ':' +
                json.dumps(pair,separators=(',',':'))).encode()).hexdigest(),16) % 60 for pair in cases]
            require(indexes == expected and all(type(x) is int for x in indexes), 'discovery-only donor plan')
    fields(trial['source_artifacts'], SOURCE_ROLES, 'source artifact roles')
    for bound in trial['source_artifacts'].values():
        fields(bound, ('bytes','sha256'), 'original binding');hash_string(bound['sha256'])
        integer(bound['bytes'],1,MAX_FILE_BYTES,'original size')
    d = trial['discovery'];fields(d, ('rows','budget'), 'discovery')
    require(len(d['rows']) == 24, 'common conditions')
    shared = {}
    for row in d['rows']:
        fields(row, ('mask','method','correct','agreement','logits','trace'), 'discovery row')
        key = row['mask'],row['method'];require(key not in shared, 'duplicate shared condition')
        shared[key] = measure(row,discovery)
    require(set(shared) == {(f'common_{i+1}',m) for i in range(8) for m in METHODS}, 'shared coverage')
    for row in observations:
        require(all(row['correct'][m] == row['agreement'][m] == shared[row['mask'],m] for m in METHODS), 'packet numerical facts')
    validate_budget(d['budget'],31,1680)
    request = trial['request'];fields(request, ('model','messages','max_tokens','temperature','stream','n'), 'request')
    require(trial['proposer_model'] == 'mlx-community/Qwen2.5-Coder-14B-Instruct-4bit' and
        request['model'] == 'forge-coder' and type(request['max_tokens']) is int and request['max_tokens'] == 64 and
        request['temperature'] == 0.0 and request['stream'] is False and request['n'] == 1, 'generation request')
    require(type(request['messages']) is list and len(request['messages']) == 2, 'message coverage')
    for row,role in zip(request['messages'],('system','user')):
        fields(row, ('role','content'), 'message');require(row['role'] == role and type(row['content']) is str, 'message role')
    compact = decode(request['messages'][1]['content'])
    fields(compact, ('source_packet_sha256','units','discovery_count','observed','eligible_choices','retain_groups','objective'), 'compact packet')
    choices = [{'choice':i+1,'omit':u} for i,u in enumerate(sorted(ids))]
    observed = [{'omit':next(iter(ids-set(r['nodes']))),'correct':r['correct'],'agreement':r['agreement']} for r in observations]
    require(compact['source_packet_sha256'] == digest(packet) and compact['units'] == packet['units'] and
            compact['observed'] == observed and compact['eligible_choices'] == choices and
            compact['discovery_count'] == 60 and compact['retain_groups'] == 15 and
            type(compact['objective']) is str, 'lossless facts/choices')
    reply = trial['reply'];fields(reply, ('raw_answer','finish_reason','usage','generation_calls','host_authored_gate_text'), 'reply')
    require(reply['finish_reason'] == 'stop' and type(reply['generation_calls']) is int and reply['generation_calls'] == 1 and
            reply['host_authored_gate_text'] is True and type(reply['raw_answer']) is str, 'proposal admission')
    raw = reply['raw_answer']
    payload = raw[8:-4] if raw.startswith('```json\n') and raw.endswith('\n```') else raw
    decision = decode(payload);fields(decision, ('choice',), 'choice')
    integer(decision['choice'],1,16,'choice range')
    fields(reply['usage'], ('prompt_tokens','completion_tokens','total_tokens'), 'usage')
    integer(reply['usage']['completion_tokens'],1,64,'output ceiling')
    integer(reply['usage']['prompt_tokens'],1,100000,'input usage')
    require(type(reply['usage']['total_tokens']) is int and reply['usage']['total_tokens'] ==
            reply['usage']['prompt_tokens'] + reply['usage']['completion_tokens'], 'usage total')
    proposal = trial['proposal'];fields(proposal, ('schema','model_id','packet_sha256','nodes','hypothesis','prediction','falsifier'), 'proposal')
    require(proposal['schema'] == 'forge_robust_joint17_proposal_v1' and proposal['model_id'] == packet['model_id'] and
            proposal['packet_sha256'] == digest(packet), 'proposal source')
    for key in ('hypothesis','prediction','falsifier'):
        require(type(proposal[key]) is str and 1 <= len(proposal[key]) <= 240 and proposal[key].startswith('Host-stated'), 'host gate text')
    validate_mask(proposal['nodes'],ids)
    require(proposal['nodes'] == sorted(ids - {choices[decision['choice']-1]['omit']}), 'choice/mask binding')
    def rank(row):
        counts = [row[k][m] for k in ('correct','agreement') for m in METHODS]
        return (-min(counts),-sum(counts),next(iter(ids-set(row['nodes']))))
    masks = {'agent':proposal['nodes'],'cheap':min(observations,key=rank)['nodes']}
    fields(trial['selection'], ('masks',), 'selection')
    require(trial['selection']['masks'] == masks, 'sealed selector identity')
    score = trial['score'];fields(score, ('discovery_candidates','controls','rows','attention_control',
        'full_correct','gates','agent_equals_cheap','budget'), 'score')
    candidates = {}
    for row in score['discovery_candidates']:
        fields(row, ('mask','method','correct','agreement','logits','trace'), 'candidate')
        key = row['mask'],row['method'];require(key not in candidates,'duplicate candidate')
        candidates[key] = measure(row,discovery)
    require(set(candidates) == {(s,m) for s in SELECTORS for m in METHODS}, 'equal candidate coverage')
    controls = {}
    for row in score['controls']:
        fields(row, ('mode','method','correct','agreement','logits','trace'), 'control')
        key = row['mode'],row['method'];require(key not in controls,'duplicate control')
        controls[key] = row;measure(row,evaluation)
    require(set(controls) == {(mode,m) for mode in ('full','empty') for m in METHODS}, 'control coverage')
    require(all(controls['full',m]['correct'] == 61 and
                controls['full',m]['logits'] == controls['full','zero']['logits'] for m in METHODS), 'full parity')
    require(controls['empty','zero']['correct'] < 31, 'empty positive control')
    paired = {}
    for row in score['rows']:
        fields(row, ('mask','method','mode','retained_units','correct','agreement','logits','trace'), 'paired row')
        key = row['mask'],row['method'],row['mode'];require(key not in paired,'duplicate paired condition')
        require(row['mask'] in SELECTORS and row['mode'] in ('keep','complement'), 'condition')
        measure(row,evaluation)
        expected = set(masks[row['mask']]) if row['mode'] == 'keep' else ids - set(masks[row['mask']])
        require(type(row['retained_units']) is list and set(row['retained_units']) == expected and
                len(row['retained_units']) == len(expected), 'retained mask')
        paired[key] = row
    require(set(paired) == {(s,m,mode) for s in SELECTORS for m in METHODS for mode in ('keep','complement')}, 'paired coverage')
    gates = {}
    for name in SELECTORS:
        keep = {m:paired[name,m,'keep'] for m in METHODS}
        comp = {m:paired[name,m,'complement'] for m in METHODS}
        gates[name] = paired_gate(keep,comp)
    require(digest(score['gates']) == digest(gates) and type(score['full_correct']) is int and score['full_correct'] == 61 and
            score['agent_equals_cheap'] is (masks['agent'] == masks['cheap']), 'gate verdict')
    ac = score['attention_control'];fields(ac, ('accuracy','max_logit_delta'), 'attention control')
    require(all(type(v) in (int,float) and math.isfinite(v) for v in ac.values()) and
            0 <= ac['accuracy'] <= .10 and 0 <= ac['max_logit_delta'] <= 1e-6, 'reported attention control')
    validate_budget(score['budget'],33,1883)
    return {'seed':seed,'gates':gates,'keep':{s:[paired[s,m,'keep']['correct'] for m in METHODS] for s in SELECTORS},
            'choice':decision['choice'],'generated_tokens':reply['usage']['completion_tokens']}


def verify(root):
    root = Path(root).resolve()
    file_count = verify_manifest(root)
    computed = [verify_seed(read(root / f'evidence/seed_{seed}.json'),seed) for seed in SEEDS]
    summary = read(root / 'RESULTS.json')
    fields(summary, ('schema','study','seeds','rows','thresholds','agent_passes','cheap_passes',
        'local_generation_calls','generated_tokens','cloud_calls','training_domain_only','research_only'), 'results')
    require(summary['schema'] == 'forge_observatory_public_results_v1' and summary['study'] == 'paired_pilot_17' and
            summary['seeds'] == list(SEEDS) and digest(summary['rows']) == digest(computed) and
            summary['thresholds'] == THRESHOLDS and summary['training_domain_only'] is True and
            summary['research_only'] is True, 'aggregate identity')
    for name in SELECTORS:
        count = sum(row['gates'][name]['pass'] for row in computed)
        require(type(summary[name+'_passes']) is int and summary[name+'_passes'] == count, 'aggregate pass count')
    require(type(summary['local_generation_calls']) is int and summary['local_generation_calls'] == 3 and type(summary['generated_tokens']) is int and
            summary['generated_tokens'] == sum(row['generated_tokens'] for row in computed) <= 192 and
            type(summary['cloud_calls']) is int and summary['cloud_calls'] == 0, 'generation accounting')
    return {'evidence_integrity':'PASS','files_verified':file_count,'seeds':list(SEEDS),
            'agent_causal_passes':summary['agent_passes'],'cheap_causal_passes':summary['cheap_passes'],
            'discovery_outcomes_checked':4320,'scoring_outcomes_checked':4374,
            'saved_logits_checked':95634,'training_outcomes_checked':363,
            'generated_tokens':summary['generated_tokens'],'inference_replays':0,
            'scope':'saved_evidence_only','execution_authenticity_proven':False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        result = verify(args.root)
    except (ValueError, KeyError, TypeError, OSError, IndexError, StopIteration) as exc:
        print(json.dumps({'evidence_integrity':'FAIL','error':str(exc)[:300]}))
        return 1
    print(json.dumps(result,indent=2,allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
