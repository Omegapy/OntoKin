"""Reproduce text-token measurements; no claim about ChatGPT's live context counter."""
import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--tokenizer-root', type=Path, required=True)
    parser.add_argument('--packet', type=Path)
    args = parser.parse_args()
    sys.path.insert(0, str(args.tokenizer_root.resolve()))
    os.environ['TIKTOKEN_CACHE_DIR'] = str(args.tokenizer_root.resolve())
    import tiktoken
    if tiktoken.__version__ != '0.12.0':
        raise ValueError('measurement requires recorded tiktoken 0.12.0')
    encoding = tiktoken.get_encoding('o200k_base')
    here = Path(__file__).resolve().parent
    root = here.parents[2]
    manifest = json.loads((here / 'PRESERVATION.json').read_text())
    originals = {x['path']: (root / x['original']).read_bytes() for x in manifest['files']}
    base = manifest['base_revision']
    registry = json.loads((root / 'docs/workflow/registry.json').read_text())
    current = json.loads((root / 'docs/workflow/CURRENT.json').read_text())
    task = current.get('active_task') or current['latest_task']
    task_files = [f'docs/workflow/tasks/{task}/{f}' for f in ['task.json', 'REQUIREMENTS.md', 'PLAN.md']]
    groups = {'edited_markdown': list(originals), 'common_startup': registry['required_reads'], 'startup_with_all_skills': registry['required_reads'] + [s['path'] for s in registry['skills']]}
    groups['startup_with_all_skills_and_current_task'] = groups['startup_with_all_skills'] + task_files
    files = {}
    def count(data):
        return len(encoding.encode(data.decode('utf-8'), disallowed_special=()))
    for path in sorted({p for paths in groups.values() for p in paths}):
        before = originals.get(path)
        if before is None:
            before = subprocess.check_output(['git', 'show', base + ':' + path], cwd=root)
        after = (root / path).read_bytes()
        files[path] = {'before_bytes': len(before), 'after_bytes': len(after), 'before_tokens': count(before), 'after_tokens': count(after), 'before_sha256': hashlib.sha256(before).hexdigest(), 'after_sha256': hashlib.sha256(after).hexdigest()}
    metrics = {}
    for name, paths in groups.items():
        totals = {key: sum(files[p][key] for p in paths) for key in ['before_bytes', 'after_bytes', 'before_tokens', 'after_tokens']}
        totals['token_reduction_percent'] = round(100 * (1 - totals['after_tokens'] / totals['before_tokens']), 3)
        totals['files'] = paths
        metrics[name] = totals
    result = {'schema_version': 1, 'encoding': 'o200k_base', 'tokenizer': 'tiktoken 0.12.0', 'encoding_sha256': '446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d', 'base_revision': base, 'current_task': task, 'measure': 'Sum of separately encoded UTF-8 files; packet count includes all glossary, framing and metadata', 'limits': 'Reproducible text-token counts under this encoding, not a measurement of the active ChatGPT model tokenizer, prompt wrappers, tools, history or conversation-length limit. No guaranteed runtime context extension.', 'groups': metrics, 'files': files}
    status_text = (root / 'STATUS.md').read_text()
    navigation = re.compile(r'^<a id="[^"\r\n]+"></a>[ \t]*\r?\n?', re.M)
    anchors = navigation.findall(status_text)
    readout = navigation.sub('', status_text).encode('utf-8')
    status_readout_tokens = count(readout)
    avoided = files['STATUS.md']['after_tokens'] - status_readout_tokens
    result['navigation_readout'] = {'rule': 'Only empty STATUS HTML anchor-only lines; all source anchors remain unchanged and are read for history/link work', 'excluded_lines': len(anchors), 'excluded_bytes': sum(len(x.encode()) for x in anchors), 'status_full_tokens': files['STATUS.md']['after_tokens'], 'status_readout_tokens': status_readout_tokens, 'tokens_avoided': avoided, 'source_file_sha256': files['STATUS.md']['after_sha256'], 'readout_sha256': hashlib.sha256(readout).hexdigest()}
    result['effective_startup'] = {}
    for name in ['common_startup', 'startup_with_all_skills', 'startup_with_all_skills_and_current_task']:
        before = metrics[name]['before_tokens']
        after = metrics[name]['after_tokens'] - avoided
        result['effective_startup'][name] = {'before_tokens': before, 'after_tokens': after, 'tokens_saved': before-after, 'reduction_percent': round(100*(1-after/before), 3)}
    if args.packet:
        packet = args.packet.read_bytes()
        entry_tokens = files[registry['entrypoint']]['after_tokens']
        packet_tokens = count(packet)
        before = metrics['startup_with_all_skills_and_current_task']['before_tokens']
        after_direct = metrics['startup_with_all_skills_and_current_task']['after_tokens']
        effective = entry_tokens + packet_tokens
        result['packet'] = {'path': args.packet.name, 'bytes': len(packet), 'sha256': hashlib.sha256(packet).hexdigest(), 'tokens_including_glossary_headers_metadata': packet_tokens, 'already_read_entrypoint_tokens': entry_tokens, 'effective_startup_tokens': effective, 'before_direct_tokens': before, 'after_direct_tokens': after_direct, 'total_reduction_percent': round(100 * (1 - effective / before), 3), 'packet_reduction_vs_new_direct_percent': round(100 * (1 - effective / after_direct), 3), 'omitted_entrypoint_counted_once': True}
    (here / 'METRICS.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'groups': {k: {a:b for a,b in v.items() if a!='files'} for k,v in metrics.items()}, 'effective_startup': result['effective_startup'], 'navigation_readout': result['navigation_readout'], 'packet': result.get('packet')}))


if __name__ == '__main__':
    main()
