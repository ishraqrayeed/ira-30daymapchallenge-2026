"""Download a complete severe-crash subset and record its provenance."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.analysis.crashes import CACHE_PREFIX, DETAIL_FIELDS, FIELDS, LAYER
from src.data.download import get_json, http_session, post_json, write_json


def download(year: int, refresh: bool = False, details: bool = False) -> Path:
    if not 2021 <= year < datetime.now(timezone.utc).year:
        raise ValueError("Choose a completed calendar year from 2021 onward")
    folder = ROOT / "data/raw/day01"
    target = folder / f"{CACHE_PREFIX}-{year}.json"
    manifest_path = folder / f"{CACHE_PREFIX}-manifest-{year}.json"
    if target.exists() and not refresh:
        manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
        if not details or manifest.get("details_requested"):
            print(f"Using cache: {target}; use --refresh to replace it")
            return target
        print(f"Enriching {year} cache with optional source details", flush=True)
    where = (
        f"first_occurrence_date >= TIMESTAMP '{year}-01-01 00:00:00' AND "
        f"first_occurrence_date < TIMESTAMP '{year + 1}-01-01 00:00:00' AND "
        "(FATALITIES > 0 OR SERIOUSLY_INJURED > 0 OR "
        "UPPER(top_traffic_accident_offense) LIKE '%TRAF - ACCIDENT - FATAL%' OR "
        "UPPER(top_traffic_accident_offense) LIKE '%TRAF - ACCIDENT - SBI%') AND "
        "(pedestrian_ind = 1 OR bicycle_ind = 1)"
    )
    with http_session() as session:
        metadata = get_json(session, LAYER, f="json")
        actual = {f["name"] for f in metadata["fields"]}
        if not set(FIELDS) <= actual:
            raise ValueError("Source schema changed; review the new fields before continuing")
        extra_fields = [name for name in DETAIL_FIELDS if name in actual] if details else []
        oid = metadata["objectIdField"]
        ids = get_json(session, LAYER + "/query", f="json", where=where, returnIdsOnly="true")
        object_ids = sorted(ids.get("objectIds") or [])
        if not object_ids or ids.get("exceededTransferLimit"):
            raise ValueError("No matching records or incomplete object IDs; review source coverage")
        if len(object_ids) != len(set(object_ids)):
            raise ValueError("Duplicate object IDs in source response")
        features = []
        size = min(500, int(metadata.get("maxRecordCount", 500)))
        for offset in range(0, len(object_ids), size):
            batch = object_ids[offset:offset + size]
            # Object-ID lists can exceed proxy URL limits even below 500 rows.
            # ArcGIS supports form-encoded POST for read-only layer queries.
            page = post_json(session, LAYER + "/query", f="json",
                            objectIds=",".join(map(str, batch)), outFields=",".join(FIELDS + extra_fields + [oid]),
                            returnGeometry="true", outSR=4326)
            if page.get("exceededTransferLimit"):
                raise ValueError("Source truncated a batch; reduce batch size")
            if page.get("spatialReference", {}).get("latestWkid", page.get("spatialReference", {}).get("wkid")) != 4326:
                raise ValueError("Source did not return requested WGS84 geometry")
            returned = page.get("features", [])
            if sorted(f["attributes"][oid] for f in returned) != batch:
                raise ValueError("Source changed during extraction; retry instead of using incomplete data")
            features.extend(returned)
            print(f"Downloaded {len(features)}/{len(object_ids)} rows")
    payload = {"spatialReference": {"wkid": 4326}, "features": features}
    digest = write_json(target, payload)
    write_json(folder / f"{CACHE_PREFIX}-schema-{year}.json", metadata)
    manifest = {"source": LAYER, "where": where, "year": year,
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "sha256": digest, "rows": len(features), "outSR": 4326,
                "details_requested": details, "detail_fields": extra_fields,
                "unavailable_detail_fields": [f for f in DETAIL_FIELDS if f not in actual] if details else [],
                "native_crs": metadata.get("extent", {}).get("spatialReference"),
                "license": "CC BY 3.0", "attribution": "City of Denver Open Data Catalog",
                "terms": "https://opendata-geospatialdenver.hub.arcgis.com/"}
    write_json(folder / f"{CACHE_PREFIX}-manifest-{year}.json", manifest)
    print(f"Cached {target}")
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--start-year", type=int)
    parser.add_argument("--end-year", type=int)
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--details", action="store_true", help="Include location, road/light conditions, and reported crash context")
    args = parser.parse_args()
    try:
        if (args.start_year is None) != (args.end_year is None):
            raise ValueError("Provide both --start-year and --end-year")
        start = args.start_year if args.start_year is not None else args.year
        end = args.end_year if args.end_year is not None else args.year
        if start > end:
            raise ValueError("Start year must not exceed end year")
        for year in range(start, end + 1):
            download(year, args.refresh, args.details)
    except Exception as exc:
        parser.exit(1, f"Download failed: {exc}\nNo substitute data was generated.\n")
