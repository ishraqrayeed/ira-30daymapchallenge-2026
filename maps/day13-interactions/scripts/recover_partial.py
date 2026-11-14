"""Recover only complete rows from truncated OpenSky responses, never a snapshot."""
import json
import re
from pathlib import Path


def recover(path):
    text = path.read_text()
    match = re.match(r'\s*\{"time":\s*(\d+),\s*"states":\s*\[', text)
    if not match:
        raise ValueError('Unrecognized response header')
    decoder = json.JSONDecoder()
    cursor = match.end()
    rows = []
    while cursor < len(text):
        try:
            row, end = decoder.raw_decode(text, cursor)
        except json.JSONDecodeError:
            break
        if not isinstance(row, list) or len(row) < 17:
            break
        rows.append(row)
        cursor = end
        while cursor < len(text) and text[cursor] in ', \r\n\t':
            cursor += 1
    output = path.with_name(path.stem + '-recovered-INCOMPLETE.json')
    output.write_text(json.dumps({
        'complete_snapshot': False,
        'warning': 'Truncated transfer; arbitrary response prefix, unsuitable for national counts or comparisons.',
        'source_file': path.name,
        'time': int(match[1]),
        'states': rows,
    }, separators=(',', ':')) + '\n')
    return output, len(rows)


if __name__ == '__main__':
    import sys
    for argument in sys.argv[1:]:
        output, count = recover(Path(argument))
        print(f'{output}: {count} complete source rows; INCOMPLETE coverage')
