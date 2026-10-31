"""Audit severity-field coverage before interpreting the Day 1 subset."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.analysis.crashes import LAYER
from src.data.download import get_json, http_session, write_json


def audit(year: int) -> dict:
    base = (
        f"first_occurrence_date >= TIMESTAMP '{year}-01-01 00:00:00' AND "
        f"first_occurrence_date < TIMESTAMP '{year + 1}-01-01 00:00:00' AND "
        "(pedestrian_ind = 1 OR bicycle_ind = 1)"
    )
    conditions = {
        "all_pedestrian_bicycle_rows": "1=1",
        "positive_injury_count_rows": "FATALITIES > 0 OR SERIOUSLY_INJURED > 0",
        "null_injury_count_rows": "FATALITIES IS NULL OR SERIOUSLY_INJURED IS NULL",
        "fatal_offense_rows": "UPPER(top_traffic_accident_offense) LIKE '%FATAL%'",
        "serious_injury_offense_rows": "UPPER(top_traffic_accident_offense) LIKE '%SBI%'",
        "severe_offense_without_positive_counts": (
            "(UPPER(top_traffic_accident_offense) LIKE '%FATAL%' OR "
            "UPPER(top_traffic_accident_offense) LIKE '%SBI%') AND "
            "(FATALITIES IS NULL OR FATALITIES <= 0) AND "
            "(SERIOUSLY_INJURED IS NULL OR SERIOUSLY_INJURED <= 0)"
        ),
    }
    report = {"year": year, "source": LAYER, "counts_are": "source rows, not deduplicated incidents"}
    with http_session() as session:
        for name, condition in conditions.items():
            result = get_json(session, LAYER + "/query", f="json",
                              where=f"({base}) AND ({condition})", returnCountOnly="true")
            report[name] = result["count"]
            print(f"{name}: {result['count']:,}")
    output = ROOT / f"data/raw/day01/coverage-audit-{year}.json"
    write_json(output, report)
    print(f"Saved {output}")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2025)
    args = parser.parse_args()
    try:
        audit(args.year)
    except Exception as exc:
        parser.exit(1, f"Coverage audit failed: {exc}\n")
