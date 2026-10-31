"""Validate and classify Denver crash events without inventing severity."""

import math

import geopandas as gpd
import pandas as pd

LAYER = (
    "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/ArcGIS/rest/services/"
    "ODC_CRIME_TRAFFICACCIDENTS5YR_P/FeatureServer/325"
)
FIELDS = ["incident_id", "first_occurrence_date", "FATALITIES", "SERIOUSLY_INJURED",
          "pedestrian_ind", "bicycle_ind", "top_traffic_accident_offense"]
CACHE_PREFIX = "ped-bike-severe-v2"
DETAIL_FIELDS = [
    "incident_address", "neighborhood_id", "road_location", "ROAD_DESCRIPTION",
    "ROAD_CONDITION", "LIGHT_CONDITION", "TU1_VEHICLE_TYPE", "TU2_VEHICLE_TYPE",
    "TU1_VEHICLE_MOVEMENT", "TU2_VEHICLE_MOVEMENT", "TU1_DRIVER_ACTION",
    "TU2_DRIVER_ACTION", "TU1_DRIVER_HUMANCONTRIBFACTOR", "TU2_DRIVER_HUMANCONTRIBFACTOR",
    "FATALITY_MODE_1", "FATALITY_MODE_2", "SERIOUSLY_INJURED_MODE_1", "SERIOUSLY_INJURED_MODE_2",
]
DETAIL_COLUMNS = {
    "location": ["incident_address"], "neighborhood": ["neighborhood_id"],
    "road_context": ["road_location", "ROAD_DESCRIPTION"],
    "road_condition": ["ROAD_CONDITION"], "light_condition": ["LIGHT_CONDITION"],
    "vehicle_types": ["TU1_VEHICLE_TYPE", "TU2_VEHICLE_TYPE"],
    "vehicle_movements": ["TU1_VEHICLE_MOVEMENT", "TU2_VEHICLE_MOVEMENT"],
    "driver_actions": ["TU1_DRIVER_ACTION", "TU2_DRIVER_ACTION"],
    "reported_factors": ["TU1_DRIVER_HUMANCONTRIBFACTOR", "TU2_DRIVER_HUMANCONTRIBFACTOR"],
    "fatality_modes": ["FATALITY_MODE_1", "FATALITY_MODE_2"],
    "serious_injury_modes": ["SERIOUSLY_INJURED_MODE_1", "SERIOUSLY_INJURED_MODE_2"],
}
PROJECTED_CRS = "EPSG:26913"  # NAD83 / UTM zone 13N; metres


def reported_values(values) -> str:
    """Keep distinct reported descriptions; never turn missing data into a claim."""
    result = sorted({str(value).strip() for value in values
                     if value is not None and pd.notna(value) and str(value).strip()})
    return " / ".join(result) if result else "Not reported"


def prepare_crashes(payload: dict, year: int | tuple[int, int]) -> tuple[gpd.GeoDataFrame, dict]:
    """Validate WGS84 ArcGIS points, then aggregate duplicate incident rows.

    A broad Denver envelope is a plausibility check, not a municipal boundary.
    Severity uses positive counts OR explicit fatal/SBI offense labels. Missing
    person counts are never inferred from an offense label.
    Duplicate coordinates for one incident must agree; conflicting events are
    excluded and counted. Multiple offense rows do not become multiple crashes.
    """
    start, end = (year, year) if isinstance(year, int) else year
    if start > end:
        raise ValueError("Start year must not exceed end year")
    sr = payload.get("spatialReference", {})
    if sr.get("latestWkid", sr.get("wkid")) != 4326:
        raise ValueError("Expected explicitly declared EPSG:4326 response geometry")
    features = payload.get("features")
    if not isinstance(features, list):
        raise ValueError("Expected an ArcGIS features list")
    stats = {"input_rows": len(features), "missing_id": 0, "invalid_date": 0,
             "outside_year": 0, "invalid_coordinate": 0, "unknown_severity": 0,
             "nonsevere_rows": 0, "conflicting_incidents": 0,
             "other_mode_rows": 0, "unknown_mode_rows": 0,
             "offense_only_severity_rows": 0}
    rows = []
    for feature in features:
        attrs = feature.get("attributes", {})
        missing = set(FIELDS) - attrs.keys()
        if missing:
            raise ValueError(f"Required fields missing: {sorted(missing)}")
        pedestrian, bicycle = attrs["pedestrian_ind"], attrs["bicycle_ind"]
        if any(value is not None and value not in (0, 1) for value in (pedestrian, bicycle)):
            stats["unknown_mode_rows"] += 1
            continue
        if pedestrian != 1 and bicycle != 1:
            key = "unknown_mode_rows" if None in (pedestrian, bicycle) else "other_mode_rows"
            stats[key] += 1
            continue
        incident = attrs["incident_id"]
        if incident is None or not str(incident).strip():
            stats["missing_id"] += 1
            continue
        raw_date = attrs["first_occurrence_date"]
        date = pd.to_datetime(raw_date, unit="ms", utc=True, errors="coerce")
        if pd.isna(date):
            stats["invalid_date"] += 1
            continue
        if not start <= date.year <= end:
            stats["outside_year"] += 1
            continue
        geom = feature.get("geometry") or {}
        x, y = geom.get("x"), geom.get("y")
        if (not isinstance(x, (float, int)) or not isinstance(y, (float, int))
                or not math.isfinite(x) or not math.isfinite(y)
                or not (-105.3 <= x <= -104.4 and 39.5 <= y <= 40.1)):
            stats["invalid_coordinate"] += 1
            continue
        counts = pd.to_numeric(pd.Series([attrs["FATALITIES"], attrs["SERIOUSLY_INJURED"]]), errors="coerce")
        if any(pd.notna(c) and (not math.isfinite(c) or c < 0 or c % 1 != 0) for c in counts):
            stats["unknown_severity"] += 1
            continue
        fatal, serious = counts.iloc[0], counts.iloc[1]
        offense = str(attrs["top_traffic_accident_offense"] or "").strip().upper()
        fatal_label = offense == "TRAF - ACCIDENT - FATAL"
        serious_label = offense == "TRAF - ACCIDENT - SBI"
        count_severe = fatal > 0 or serious > 0
        if not (count_severe or fatal_label or serious_label):
            key = "unknown_severity" if counts.isna().any() else "nonsevere_rows"
            stats[key] += 1
            continue
        if not count_severe:
            stats["offense_only_severity_rows"] += 1
        details = {column: (reported_values(attrs.get(name) for name in names)
                            if any(name in attrs for name in names) else "Not in snapshot")
                   for column, names in DETAIL_COLUMNS.items()}
        rows.append({"incident_id": str(incident), "longitude": x, "latitude": y,
                     "year": int(date.year),
                     "occurrence_utc": date.strftime("%d %b %Y, %H:%M UTC"),
                     "occurrence_denver": date.tz_convert("America/Denver").strftime("%d %b %Y, %H:%M %Z"),
                     "severity_basis": "Counts and offense label" if count_severe and (fatal_label or serious_label)
                     else "Reported injury counts" if count_severe else "Offense label",
                     "fatal": int(fatal > 0 or fatal_label),
                     "serious": int(serious > 0 or serious_label),
                     "pedestrian": int(pedestrian == 1), "bicycle": int(bicycle == 1), **details})
    if not rows:
        raise ValueError(f"No validated severe crashes in {year}; QA: {stats}")
    frame = pd.DataFrame(rows)
    conflicts = frame.groupby("incident_id")[["longitude", "latitude", "year"]].nunique().max(axis=1) > 1
    stats["conflicting_incidents"] = int(conflicts.sum())
    frame = frame[~frame.incident_id.isin(conflicts[conflicts].index)]
    stats["duplicate_rows_collapsed"] = int(len(frame) - frame.incident_id.nunique())
    def descriptions(series):
        present = [value for value in series if value not in ("Not reported", "Not in snapshot")]
        return reported_values(present) if present else ("Not reported" if "Not reported" in set(series) else "Not in snapshot")

    aggregation = {"longitude": "first", "latitude": "first", "year": "first",
                   "fatal": "max", "serious": "max", "pedestrian": "max", "bicycle": "max",
                   "occurrence_utc": descriptions, "occurrence_denver": descriptions,
                   "severity_basis": descriptions,
                   **{column: descriptions for column in DETAIL_COLUMNS}}
    frame = frame.groupby("incident_id", as_index=False).agg(aggregation)
    frame["involvement"] = frame.apply(
        lambda row: "Pedestrian and bicycle" if row.pedestrian and row.bicycle
        else "Pedestrian" if row.pedestrian else "Bicycle", axis=1)
    frame["severity"] = frame.fatal.map({1: "Fatal", 0: "Serious injury"})
    if frame.empty:
        raise ValueError("No crashes remain after resolving conflicting locations")
    stats["mapped_incidents"] = int(len(frame))
    stats["fatal_crashes"] = int(frame.fatal.sum())
    stats["serious_injury_only_crashes"] = int((frame.fatal == 0).sum())
    stats["year"] = year
    stats["annual_counts"] = [
        {"year": y, "mapped_incidents": int((frame.year == y).sum()),
         "fatal_crashes": int(((frame.year == y) & (frame.fatal == 1)).sum()),
         "serious_injury_only_crashes": int(((frame.year == y) & (frame.fatal == 0)).sum())}
        for y in range(start, end + 1)]
    stats["pedestrian_involved_crashes"] = int(frame.pedestrian.sum())
    stats["bicycle_involved_crashes"] = int(frame.bicycle.sum())
    stats["both_modes_crashes"] = int(((frame.pedestrian == 1) & (frame.bicycle == 1)).sum())
    stats["scope"] = "Pedestrian- or bicycle-involved severe crashes identified by counts or explicit offense labels"
    stats["detail_coverage"] = {column: int((~frame[column].isin(["Not reported", "Not in snapshot"])).sum())
                                for column in DETAIL_COLUMNS}
    geo = gpd.GeoDataFrame(frame, geometry=gpd.points_from_xy(frame.longitude, frame.latitude), crs=4326)
    return geo.to_crs(PROJECTED_CRS), stats
