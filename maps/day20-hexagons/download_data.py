"""Cache a bounded set of public evidence pages and record response provenance."""
import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
CACHE = HERE.parents[1] / "data/raw/day20-hexagons"


def collect(refresh, only=()):
    CACHE.mkdir(parents=True, exist_ok=True)
    manifest_path = HERE / "source-manifest.json"
    previous = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    known = {row["id"]: row for row in previous}
    manifest = []
    with (HERE / "sources.tsv").open() as source:
        for row in csv.DictReader(source, delimiter="\t"):
            if only and row["id"] not in only:
                if row["id"] in known:
                    manifest.append(known[row["id"]])
                continue
            destination = CACHE / row["id"]
            old = known.get(row["id"], {})
            if not refresh and destination.exists() and old.get("url") == row["url"]:
                if hashlib.sha256(destination.read_bytes()).hexdigest() == old.get("sha256"):
                    manifest.append(old)
                    continue
            temporary = destination.with_suffix(".partial")
            result = subprocess.run(
                ["curl", "-LsS", "--max-time", "120" if row["id"] == "nat-pop-bulk" else "20", "-o", str(temporary),
                 "-w", "%{http_code}\t%{url_effective}\t%{content_type}", row["url"]],
                capture_output=True, text=True,
            )
            status, final_url, content_type = (result.stdout.split("\t") + ["", "", ""])[:3]
            body = temporary.read_bytes() if temporary.exists() else b""
            if temporary.exists():
                temporary.replace(destination)
            record = dict(row, retrieved_utc=datetime.now(timezone.utc).date().isoformat(),
                          http_status=status, final_url=final_url, content_type=content_type,
                          bytes=len(body), sha256=hashlib.sha256(body).hexdigest() if body else "",
                          error=result.stderr.strip())
            manifest.append(record)
            print(row["id"], status, len(body), record["error"], flush=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--only", nargs="+", default=())
    selection.add_argument("--clubs", action="store_true", help="Collect only the club-map inputs.")
    args = parser.parse_args()
    keys = args.only
    if args.clubs:
        with (HERE / "sources.tsv").open() as stream:
            keys = [row["id"] for row in csv.DictReader(stream, delimiter="\t")
                    if re.fullmatch(r"nat-usclub-national-(?:test|\d+)|nat-usclub-states|nat-boundaries", row["id"])]
    collect(args.refresh, keys)
