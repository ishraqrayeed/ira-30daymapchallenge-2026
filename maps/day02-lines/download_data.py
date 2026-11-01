"""Cache authoritative public NPS trails/boundary and a USGS elevation grid."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

import rasterio
from shapely.geometry import shape
from shapely.ops import transform, unary_union
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data.download import get_json, http_session, write_json

CACHE = ROOT / "data/raw/day02-lines"
TRAILS = "https://mapservices.nps.gov/arcgis/rest/services/NationalDatasets/NPS_Public_Trails/FeatureServer/0"
BOUNDARY = "https://services1.arcgis.com/fBc8EJBxQRMcHlei/arcgis/rest/services/NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer/2"
ELEVATION = "https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer"


def fetch_features(session, url, where):
    """Batch by object ID, and reject partial responses."""
    try:
        ids = get_json(session, url + "/query", f="json", where=where, returnIdsOnly="true")
    except ValueError:
        # Some NPS services advertise ID queries but reject them. Page a stable
        # OBJECTID order until a non-truncated final page, checking uniqueness.
        features = []
        offset = 0
        while True:
            result = get_json(session, url + "/query", f="geojson", where=where,
                              outFields="*", outSR=4326, returnZ="false", returnM="false",
                              orderByFields="OBJECTID", resultOffset=offset, resultRecordCount=500)
            page = result["features"]
            features.extend(page)
            if not result.get("exceededTransferLimit") and len(page) < 500:
                break
            if not page:
                raise ValueError("Empty truncated page")
            offset += len(page)
        identifiers = [f["properties"]["OBJECTID"] for f in features]
        if not features or len(set(identifiers)) != len(features):
            raise ValueError("Empty or duplicate paginated features")
        return {"type": "FeatureCollection", "features": features}
    object_ids = sorted(ids.get("objectIds") or [])
    if not object_ids:
        raise ValueError(f"No features matched {where}")
    features = []
    for offset in range(0, len(object_ids), 150):
        result = get_json(session, url + "/query", f="geojson",
                          objectIds=",".join(map(str, object_ids[offset:offset + 150])),
                          outFields="*", outSR=4326, returnZ="false", returnM="false")
        if result.get("exceededTransferLimit"):
            raise ValueError("Feature response was truncated")
        features.extend(result["features"])
    if len(features) != len(object_ids):
        raise ValueError("Object ID and feature counts disagree")
    return {"type": "FeatureCollection", "features": features}


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    session = http_session()
    manifest = {"retrieved_utc": datetime.now(timezone.utc).isoformat(), "sources": {}}
    for name, url, where in [("trails", TRAILS, "UNITCODE = 'ROMO'"),
                             ("boundary", BOUNDARY, "UNIT_CODE = 'ROMO' AND Status = 'Official'")]:
        path = CACHE / f"{name}.geojson"
        if not path.exists():
            print(f"Fetching {name}", flush=True)
            write_json(path, fetch_features(session, url, where))
        metadata_path = CACHE / f"{name}.metadata.json"
        if not metadata_path.exists():
            write_json(metadata_path, get_json(session, url, f="json"))
        manifest["sources"][name] = {"url": url, "where": where,
                                       "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    boundary = json.loads((CACHE / "boundary.geojson").read_text())
    project = Transformer.from_crs(4326, 26913, always_xy=True).transform
    park = transform(project, unary_union([shape(f["geometry"]) for f in boundary["features"]]))
    xmin, ymin, xmax, ymax = park.bounds
    cx, cy = (xmin + xmax) / 2, (ymin + ymax) / 2
    # Circumscribe the whole park, including detached eastern parcels, with margin.
    radius = max(((x - cx)**2 + (y - cy)**2)**0.5
                 for polygon in (park.geoms if hasattr(park, "geoms") else [park])
                 for x, y in polygon.exterior.coords) * 1.10
    bounds = [cx - radius, cy - radius, cx + radius, cy + radius]
    grid = CACHE / "elevation.tif"
    params = dict(bbox=",".join(map(str, bounds)), bboxSR=26913, imageSR=26913,
                  size="2400,2400", format="tiff", pixelType="F32",
                  interpolation="RSP_BilinearInterpolation",
                  renderingRule=json.dumps({"rasterFunction": "None"}), f="image")
    if not grid.exists():
        print("Fetching USGS bare-earth elevation grid", flush=True)
        response = session.get(ELEVATION + "/exportImage", params=params, timeout=(15, 180))
        response.raise_for_status()
        if "json" in response.headers.get("Content-Type", ""):
            raise ValueError(response.text)
        temporary = CACHE / "elevation.download.tif"
        temporary.write_bytes(response.content)
        with rasterio.open(temporary) as dataset:
            if dataset.count != 1 or dataset.crs.to_epsg() != 26913:
                raise ValueError("Unexpected elevation grid CRS or band count")
            values = dataset.read(1, masked=True)
            if values.count() != values.size or values.min() < 0 or values.max() > 5000:
                raise ValueError("Missing or implausible elevation values")
        temporary.replace(grid)
    if not (CACHE / "elevation.metadata.json").exists():
        write_json(CACHE / "elevation.metadata.json", get_json(session, ELEVATION, f="json"))
    manifest["sources"]["elevation"] = {"url": ELEVATION, "parameters": params,
        "sha256": hashlib.sha256(grid.read_bytes()).hexdigest()}
    # Preserve the original retrieval timestamp when regenerating from cache.
    if not (CACHE / "manifest.json").exists():
        write_json(CACHE / "manifest.json", manifest)
    print(f"Source cache ready: {CACHE}")


if __name__ == "__main__":
    main()
