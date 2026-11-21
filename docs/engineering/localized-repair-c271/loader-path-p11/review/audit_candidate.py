"""Independent inert-artifact audit. Never imports or calls OntoKin product code.

This checks exact records, independently decodes fixed ELF/auxv bytes, and records
the facts supplied to each future control. It is not a loader implementation or
an operational acceptance predicate. All filesystem reads concern supplied
artifacts and cited source files; logical /fixture and /proc paths are not read.
"""
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import struct
import sys

WORKSPACE = Path('/workspace/scratch/2ad494d5da19')
AUTHOR = WORKSPACE / 'session_evidence/loader_design'
OUT_ROOT = WORKSPACE / 'session_evidence/design_review'
candidate = (AUTHOR / sys.argv[1]).resolve()
out = OUT_ROOT / sys.argv[1]
out.mkdir(exist_ok=False)
checks = []


def check(label, condition, detail=None):
    checks.append({'check': label, 'pass': bool(condition), 'detail': detail})


def load(path):
    return json.loads(path.read_text())


def digest(data):
    return hashlib.sha256(data).hexdigest()


def binding(path):
    raw = path.read_bytes()
    return {'size_bytes': len(raw), 'sha256': digest(raw),
            'mode': oct(stat.S_IMODE(path.lstat().st_mode))}


def verify(row, base, label, allowed_root):
    p = base / row['path']
    check(label + ': inside allowed evidence root', p.resolve().is_relative_to(allowed_root))
    s = p.lstat()
    check(label + ': inert regular unique file', stat.S_ISREG(s.st_mode) and not p.is_symlink() and s.st_nlink == 1)
    actual = binding(p)
    check(label + ': exact binding', all(actual[k] == row[k] for k in ('size_bytes', 'sha256', 'mode') if k in row),
          {'declared': row, 'actual': actual})
    return actual


def concise(value):
    rendered = json.dumps(value, sort_keys=True, ensure_ascii=True)
    return value if len(rendered) <= 180 else {'preview': rendered[:150], 'rendered_length': len(rendered), 'sha256': digest(rendered.encode())}


def differences(a, b, pointer=''):
    if type(a) is not type(b):
        return [{'pointer': pointer, 'before': concise(a), 'after': concise(b)}]
    if isinstance(a, dict):
        rows = []
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                rows.append({'pointer': pointer + '/' + k, 'before': concise(a.get(k, '<absent>')), 'after': concise(b.get(k, '<absent>'))})
            else:
                rows += differences(a[k], b[k], pointer + '/' + k)
        return rows
    if isinstance(a, list):
        if len(a) != len(b):
            return [{'pointer': pointer, 'before': concise(a), 'after': concise(b)}]
        rows = []
        for i, (x, y) in enumerate(zip(a, b)):
            rows += differences(x, y, pointer + '/' + str(i))
        return rows
    return [] if a == b else [{'pointer': pointer, 'before': concise(a), 'after': concise(b)}]


manifest_path = candidate / 'CANDIDATE-MANIFEST.json'
manifest = load(manifest_path)
manifest_binding = binding(manifest_path)
if candidate.name == 'candidate002':
    check('Exact requested immutable candidate002 manifest', manifest_binding['sha256'] == '563e84cc83f31a202cc0eead9102b66b08050ea011dfbbf4ed6fc19db318c8f4' and manifest_binding['size_bytes'] == 30583)
check('Candidate declaration has no product execution/qualification', manifest['product_execution'] is False and manifest['host_qualification'] is False and manifest['product_files_changed'] == [])
payload = manifest['payload']
names = [r['path'] for r in payload]
check('Payload paths unique', len(names) == len(set(names)))
check('Payload paths normalized relative', all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts and str(PurePosixPath(n)) == n for n in names))
observed = {str(p.relative_to(candidate)) for p in candidate.rglob('*') if p.is_file() or p.is_symlink()}
check('Complete exact payload inventory', observed == set(names) | {'CANDIDATE-MANIFEST.json'}, {'extra': sorted(observed - set(names) - {'CANDIDATE-MANIFEST.json'}), 'missing': sorted(set(names) - observed)})
for r in payload:
    verify(r, candidate, 'payload/' + r['path'], candidate)
for r in manifest['supporting_files']:
    verify(r, candidate, 'support/' + r['path'], AUTHOR)

fixture = load(candidate / 'FIXTURE-MANIFEST.json')
expectation_document = load(candidate / 'EXPECTATIONS.json')
expected = expectation_document['cases']
construction = load(candidate / 'CONSTRUCTION.json')
file_rows = {r['path']: r for r in fixture['files']}
check('Exact unique fixture inventory', len(file_rows) == len(fixture['files']) and set(file_rows) == {str(p.relative_to(candidate)) for p in (candidate / 'fixture_inputs').iterdir()})
for name, row in file_rows.items():
    check(name + ': frozen nonexecutable fixture mode', row['mode'] == '0o600' and binding(candidate / name)['mode'] == '0o600')
check('Oracle declares independent, unexecuted scope', expectation_document['derived_from_production_output'] is False and expectation_document['production_parser_calls'] == 0 and fixture['operational'] is False and fixture['actual_product_execution'] == 'not_run')

elf_facts = {}
for label, spec in construction['elf_layouts'].items():
    name = spec['binding']['path']
    raw = (candidate / name).read_bytes()
    check(label + ': construction binding equals frozen file', spec['binding'] == file_rows[name])
    h = struct.unpack_from('<16sHHIQQQIHHHHHH', raw)
    ident, elf_type, machine, version, entry, phoff, shoff, flags, ehsize, phsize, phnum, shsize, shnum, shstr = h
    check(label + ': independent ELF64 LE header', ident[:7] == b'\x7fELF\x02\x01\x01' and version == 1 and ehsize == 64 and phsize == 56 and phoff + phnum * phsize <= len(raw))
    headers = [struct.unpack_from('<IIQQQQQQ', raw, phoff + i * phsize) for i in range(phnum)]
    check(label + ': independently decoded header matches construction', raw[:ehsize].hex() == spec['elf_header_hex'] and [list(v) for v in headers] == spec['program_headers'])
    check(label + ': inert segment permissions', all(p[1] & 1 == 0 for p in headers))
    loads = [p for p in headers if p[0] == 1]
    dynamic = [p for p in headers if p[0] == 2]
    interp = [p for p in headers if p[0] == 3]
    check(label + ': finite dynamic and interpreter segments', len(dynamic) == 1 and len(interp) == 1)
    dy = dynamic[0]
    entries = [struct.unpack_from('<qQ', raw, i) for i in range(dy[2], dy[2] + dy[5], 16)]
    check(label + ': independently decoded dynamic table matches construction', [list(v) for v in entries] == spec['dynamic_entries'] and entries[-1] == (0, 0))
    values = {}
    for tag, val in entries:
        values.setdefault(tag, []).append(val)
    straddr, strsize = values[5][0], values[10][0]
    mappings = [p[2] + straddr - p[3] for p in loads if p[3] <= straddr and straddr + strsize <= p[3] + p[5]]
    check(label + ': unique independently derived string table map', len(mappings) == 1)
    offset = mappings[0]
    strings = raw[offset:offset + strsize]
    check(label + ': raw string bytes and offsets match construction', offset == spec['string_table_offset'] and strings.hex() == spec['string_table_hex'] and len(strings) == strsize)

    def string_at(pos):
        end = strings.index(b'\0', pos)
        return strings[pos:end].decode('ascii')

    interpreter = raw[interp[0][2]:interp[0][2] + interp[0][5]]
    check(label + ': raw interpreter matches construction', interpreter.hex() == spec['interpreter_hex'] and interpreter[-1:] == b'\0')
    metadata = {'class': 64, 'endian': 'little', 'type': elf_type, 'machine': machine,
                'interpreter': interpreter[:-1].decode('ascii'),
                'needed': [string_at(v) for v in values.get(1, [])],
                'soname': string_at(values[14][0]) if 14 in values else None,
                'rpath': string_at(values[15][0]).split(':') if 15 in values else [],
                'runpath': string_at(values[29][0]).split(':') if 29 in values else []}
    check(label + ': independently decoded raw metadata equals construction', metadata == spec['raw_expected_metadata'])
    for field in spec['fields']:
        check(label + ': raw string field at ' + str(field['offset']), strings[field['offset']:field['offset'] + len(bytes.fromhex(field['raw_hex']))] == bytes.fromhex(field['raw_hex']) == field['text'].encode('ascii') + b'\0')
    elf_facts[name] = {'header': {'class': 64, 'machine': machine, 'type': elf_type},
                       'program_headers': [list(p) for p in headers], 'dynamic_entries': [list(p) for p in entries],
                       'metadata': metadata, 'flags': values.get(30, []), 'flags1': values.get(0x6ffffffb, []),
                       'duplicate_tags': sorted(t for t, v in values.items() if t not in (0, 1) and len(v) > 1)}

aux_facts = {}
aux_specs = [x['binding'] for x in construction['auxiliary_vectors'].values()] + [construction['truncated_auxiliary_vector']]
for desc in aux_specs:
    raw = (candidate / desc['path']).read_bytes()
    pairs = [list(struct.unpack_from('<QQ', raw, i)) for i in range(0, len(raw) - len(raw) % 16, 16)]
    aux_facts[desc['path']] = {'size_bytes': len(raw), 'pair_count': len(pairs), 'remainder_bytes': len(raw) % 16,
                             'secure_values': [v for t, v in pairs if t == 23],
                             'terminator_indexes': [i for i, (t, v) in enumerate(pairs) if t == 0],
                             'terminator_values': [v for t, v in pairs if t == 0]}
    check(desc['path'] + ': exact auxiliary descriptor', desc == file_rows[desc['path']])
for label, spec in construction['auxiliary_vectors'].items():
    raw = (candidate / spec['binding']['path']).read_bytes()
    pairs = [list(v) for v in struct.iter_unpack('<QQ', raw)]
    check(label + ': independently decoded auxiliary pairs', pairs == spec['pairs'])

base = load(candidate / 'fixture_inputs/P01_nonselecting_base.json')
case_facts = []
case_ids = [c['id'] for c in fixture['cases']]
check('Exact unique oracle case mapping', len(case_ids) == len(set(case_ids)) and set(case_ids) == set(expected))
for row in fixture['cases']:
    ident = row['id']
    ctx = load(candidate / row['input']['path'])
    ex = expected[ident]
    raw_meta = elf_facts[row['image']['path']]['metadata']
    check(ident + ': exact context/image binding', row['input'] == file_rows[row['input']['path']] and row['image'] == file_rows[row['image']['path']] == ctx['image'] and row['expected_key'] == ident)
    check(ident + ': no operational positive or starts', ctx['operational'] is False and ex['host_qualified'] is False and ex['target_starts'] == 0)
    facts = {'id': ident, 'route': row['route'], 'mutation': row['mutation'], 'expected': ex,
             'image': row['image'], 'decoded_metadata': raw_meta}
    if 'subject' in ctx:
        check(ident + ': actual subject bytes truthfully bind synthetic image', ctx['subject']['actual_bytes'] == row['image'])
        check(ident + ': operational pin remains exact', ctx['subject']['operational_pin'] == {'mode': '0o755', 'sha256': 'fa67443527ed9647f760d807e2a38f26340757123e643c4639cf273ed15d5ea7', 'size_bytes': 30894944})
        paths = {'subject': ctx['subject']['path'], 'origin': ctx['origin_claim'], 'pre_normalization': ctx['origin_claim'] + '/../lib'}
        paths.update({'expanded/' + str(i): p for i, p in enumerate(ctx['expanded_claim'])})
        paths.update({'variant/' + str(i): p['path'] for i, p in enumerate(ctx['variants'])})
        facts['path_dimensions'] = {k: {'utf8_bytes': len(p.encode('utf-8')), 'characters': len(p), 'parts_including_root': len(PurePosixPath(p).parts)} for k, p in paths.items()}
        facts['finite_counts'] = {'needed_names': len(ctx['needed_names_claim']), 'suffixes': len(ctx['variant_review']['suffixes']),
                                  'variants': len(ctx['variants']), 'present_variants': sum(p['state'] == 'directory' for p in ctx['variants']),
                                  'candidate_product': sum(p['state'] == 'directory' for p in ctx['variants']) * len(ctx['needed_names_claim']),
                                  'maximum_needed_per_image': max([len(p['needed']) for p in ctx['closure_images']] or [0]),
                                  'declared_guard_count': len(ctx['guards']), 'search_directories': len(ctx['search_directories'])}
        facts['auxv'] = aux_facts[ctx['kernel']['auxv']['path']]
        facts['delta_from_P01'] = differences(base, ctx)
        facts['candidate_matches'] = [{'path': p, 'name': n, 'entry': entries['entries'][n]} for p, entries in ctx['search_directories'].items() for n in ctx['needed_names_claim'] if n in entries['entries']]
    if ex['outcome'] == 'metadata':
        check(ident + ': exact legacy raw success', ex['value'] == raw_meta)
    elif ex['outcome'] == 'rule_acceptance':
        check(ident + ': synthetic-only expected outcome', ex['accepted_for'] == 'synthetic_private_rule_only' and ex['metadata'] == raw_meta and ex['raw_rpath'] == ['$ORIGIN/../lib'] and ex['runpath'] == [])
        check(ident + ': exact expected origin transformation', ex['origin'] == ctx['origin_claim'] == str(PurePosixPath(ctx['subject']['path']).parent) and ex['expanded_rpath'] == ctx['expanded_claim'] == [str(PurePosixPath(ctx['origin_claim']).parent / 'lib')])
        check(ident + ': synthetic positive path and cardinality bounds', all(v['utf8_bytes'] <= 4096 and v['parts_including_root'] <= 128 for v in facts['path_dimensions'].values()) and facts['finite_counts']['needed_names'] <= 4096 and facts['finite_counts']['suffixes'] <= 128 and facts['finite_counts']['candidate_product'] <= 32768)
        check(ident + ': positive nonselecting entries', not facts['candidate_matches'])
        check(ident + ': complete synthetic union', ctx['needed_names_claim'] == sorted({n for image in ctx['closure_images'] for n in image['needed']}))
        check(ident + ': exact synthetic variant inventory', [v['suffix'] for v in ctx['variants']] == ctx['variant_review']['suffixes'] and all(v['path'] == str(PurePosixPath(ctx['expanded_claim'][0]) / v['suffix']) for v in ctx['variants']))
        check(ident + ': positive secure witness', facts['auxv']['secure_values'] == [0] and facts['auxv']['pair_count'] <= 256 and facts['auxv']['remainder_bytes'] == 0 and facts['auxv']['terminator_indexes'] == [facts['auxv']['pair_count'] - 1] and facts['auxv']['terminator_values'] == [0] and type(ctx['kernel']['at_secure_claim']) is int and ctx['kernel']['at_secure_claim'] == 0)
        check(ident + ': positive exact logical image identity', ctx['subject']['kind'] == 'file' and ctx['subject']['mode'] == '0o755' and ctx['subject']['nlink'] == 1 and ctx['kernel']['proc_exe_path'] == ctx['subject']['path'] and ctx['kernel']['proc_file_identity'] == {k:ctx['subject'][k] for k in ('device','inode')})
        check(ident + ': positive nonsymlink directories', all(v['kind'] == 'directory' and v['target'] is None for v in ctx['guards']))
    elif ex['outcome'] == 'refusal':
        check(ident + ': exact normative refusal selectors', ex['state'] == 'REJECTED' and ex['code'].startswith('CHI-') and bool(ex['stage']) and bool(ex['rule_id']))
    elif ex['outcome'] == 'propagated_callback':
        check(ident + ': exact callback sentinel and stage', ex['exception_identity'] == ctx['fault']['exception_identity'] and ex['stage'] == ctx['fault']['at'])
    else:
        check(ident + ': known expected outcome', False)
    case_facts.append(facts)

sources = load(candidate / 'SOURCES.json')
source_rows = []
for row in sources['local']:
    actual = verify(row, WORKSPACE, 'cited source/' + row['id'], WORKSPACE)
    source_rows.append({'id': row['id'], 'path': row['path'], 'actual': actual})
protected = load(candidate / 'PROTECTED-SOURCES.json')
for row in protected['files']:
    verify(row, WORKSPACE / 'OntoKin', 'protected source/' + row['path'], WORKSPACE / 'OntoKin')

# A source-only inventory records author helper imports/call spellings; it does
# not execute them, and cannot independently prove all historical behavior.
helper_ast = []
for row in manifest['supporting_files']:
    if not row['path'].endswith('.py'):
        continue
    p = candidate / row['path']
    tree = ast.parse(p.read_text())
    imports = sorted({ast.unparse(n) for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))})
    calls = sorted({ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)})
    helper_ast.append({'path': row['path'], 'imports': imports, 'call_names': calls})
    check(row['path'] + ': no product/runtime import', not any('current_host_inspection' in x or 'subprocess' in x or 'ctypes' in x for x in imports))

for name, value in [('CHECKS.json', checks), ('ELF-FACTS.json', elf_facts), ('AUXV-FACTS.json', aux_facts), ('CASE-FACTS.json', case_facts), ('SOURCE-FACTS.json', source_rows), ('AUTHOR-HELPER-AST.json', helper_ast)]:
    (out / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
report = {'schema': 'ontokin.c271.p11-independent-static-audit/1', 'candidate': candidate.name,
          'candidate_manifest': {'path': str(manifest_path), **manifest_binding},
          'reviewer_script': {'path': str(Path(__file__).resolve()), **binding(Path(__file__))},
          'checks': len(checks), 'passed': sum(c['pass'] for c in checks),
          'failed': [c for c in checks if not c['pass']],
          'counts': {'payload': len(payload), 'supporting_files': len(manifest['supporting_files']), 'fixtures': len(file_rows), 'cases': len(case_ids), 'ELF_images': len(elf_facts), 'auxv_assets': len(aux_facts), 'local_sources': len(sources['local']), 'protected_sources': len(protected['files'])},
          'product_imports': 0, 'product_calls': 0, 'host_observations': 0, 'target_executions': 0,
          'scope': 'Independent raw-byte, source-identity and synthetic-input consistency evidence only; separate report adjudicates design and control adequacy.'}
(out / 'STATIC-REVIEW.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps(report, indent=2, sort_keys=True))
sys.exit(0 if not report['failed'] else 1)
