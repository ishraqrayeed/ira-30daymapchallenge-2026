"""Fetch pinned public GitHub files; never scrape a football provider."""
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CACHE = ROOT / 'data/raw/day05-sight'


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((HERE / 'source-manifest.json').read_text())
    for item in manifest['files']:
        path = CACHE / item['cache_name']
        if not path.exists():
            request = Request(item['url'], headers={'User-Agent': '30DayMapChallenge-research/1.0'})
            with urlopen(request, timeout=45) as response:
                payload = response.read()
            if hashlib.sha256(payload).hexdigest() != item['sha256']:
                raise ValueError(f"Source checksum changed: {path.name}")
            path.write_bytes(payload)
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError(f"Cache checksum mismatch: {path.name}")
        print(f'Verified {path.name}')


if __name__ == '__main__':
    main()
