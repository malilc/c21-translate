"""Validate full story coverage against the offline source catalogs."""
import collections
import hashlib
import json
import pathlib
import re

root = pathlib.Path(__file__).resolve().parents[2]

def entries(path):
    data = json.loads(path.read_text(encoding='utf-8-sig'))
    return data if isinstance(data, list) else data['Entries']

def decode(value):
    return re.sub(r'\\(\\|n|r|t|u001b)', lambda m: {
        '\\': '\\', 'n': '\n', 'r': '\r', 't': '\t', 'u001b': '\x1b'
    }[m[1]], value)

report = []
all_sources = set()
for part in 'abc':
    original = entries(root / ('config/full-story-' + part + '.json'))
    translated = entries(root / ('config/english-expanded/story-' + part + '.json'))
    expected = {decode(e['SourceEscaped']) for e in original}
    seen = set()
    unchanged = []
    for entry in translated:
        source, target = (decode(entry[k]) for k in ['SourceEscaped', 'TargetEscaped'])
        assert source in expected, ('Unexpected source', part, source)
        assert source not in seen, ('Duplicate source', part, source)
        seen.add(source)
        assert hashlib.sha256(source.encode('utf-8')).hexdigest().upper() == entry['SourceUtf8Sha256'].upper()
        assert not re.search('[\u0e00-\u0e7f]', target), ('Thai residue', part, source)
        assert target or not source, ('Empty translation', part, source)
        assert re.findall('\x1b.', source) == re.findall('\x1b.', target), ('Color controls', part, source)
        assert collections.Counter(c for c in source if c in '\n\r\t') == collections.Counter(c for c in target if c in '\n\r\t'), ('Line controls', part, source)
        if source == target:
            unchanged.append(source)
    assert seen == expected, ('Missing sources', part, len(expected - seen))
    all_sources.update(seen)
    report.append({'part': part, 'sourceRows': len(original), 'uniqueSources': len(expected), 'unchanged': unchanged})

print(json.dumps({'status': 'PASS', 'uniqueSources': len(all_sources), 'catalogs': report}, ensure_ascii=False, indent=2))
