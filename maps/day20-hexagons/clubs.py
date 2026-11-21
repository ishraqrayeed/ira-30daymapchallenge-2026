"""Build a nationwide snapshot of geocoded US Club Soccer directory locations."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import re
import subprocess
from urllib.parse import urlsplit

import h3

from download_data import CACHE, HERE
import main as pilot

OUT = HERE / "outputs/clubs"
GEOCODER = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
STATES = set("AK AL AR AZ CA CO CT DC DE FL GA HI IA ID IL IN KS KY LA MA MD ME MI MN MO MS MT NC ND NE NH NJ NM NV NY OH OK OR PA RI SC SD TN TX UT VA VT WA WI WV WY".split())


def pages():
    manifest = json.loads((HERE / "source-manifest.json").read_text())
    indexed = [m for m in manifest if re.fullmatch(r"nat-usclub-national-(?:test|\d+)", m["id"])]
    clubs, numbers, totals, listings = {}, set(), set(), []
    count = 0
    for entry in indexed:
        payload = json.loads((CACHE / entry["id"]).read_text())
        entries = payload["clubs"]
        assert len(entries) == payload["records_on_page"]
        numbers.add(payload["page"])
        totals.add(payload["total_records"])
        count += len(entries)
        for club in entries:
            record = dict(club, source_url=entry["url"], retrieved_utc=entry["retrieved_utc"])
            clubs.setdefault(club["id"], record)
            listings.append(record)
    assert len(totals) == 1, totals
    total, = totals
    assert numbers == set(range(1, (total + 99)//100 + 1)), numbers
    return clubs, dict(advertised_total=total, pages=len(numbers), records_downloaded=count,
                       unique_directory_ids=len(clubs), duplicate_records=count-len(clubs)), listings


def eligibility(club):
    return (club["state"] in STATES and club["country"] == "US"
            and club["org_type"].strip().casefold() == "club" and club["team_count"] > 0)


def address(club):
    street = club["address1"].strip()
    street = re.split(r"(?i)\s+(?:suite|ste\.?|apt\.?|unit|#)\s*\w+", street, maxsplit=1)[0].strip(" ,")
    if not re.match(r"^\d", street) or not (club["city"] or club["zipcode"]):
        return None
    return street, club["city"], club["state"], club["zipcode"][:5]


def geocodes(clubs, fetch):
    addresses = defaultdict(list)
    for club in clubs:
        usable = address(club)
        if usable:
            addresses[usable].append(club["id"])
    result, log = {}, []
    entries = sorted(addresses.items())
    for start in range(0, len(entries), 1000):
        segment = entries[start:start+1000]
        stream = io.StringIO()
        index = {}
        writer = csv.writer(stream, lineterminator="\n")
        for key, (location, ids) in enumerate(segment):
            index[str(key)] = (location, ids)
            writer.writerow([key, *location])
        body = stream.getvalue().encode()
        digest = hashlib.sha256(body).hexdigest()
        request = CACHE / f"census-clubs-{digest[:16]}-input.csv"
        cached = CACHE / f"census-clubs-{digest[:16]}-results.csv"
        request.write_bytes(body)
        if fetch and not cached.exists():
            response = subprocess.run(["curl", "-fLsS", "--max-time", "150", "-F",
                                       f"addressFile=@{request};type=text/csv", "-F", "benchmark=Public_AR_Current",
                                       GEOCODER], capture_output=True)
            if response.returncode == 0 and response.stdout and not response.stdout.lstrip().startswith(b"<"):
                cached.write_bytes(response.stdout)
            else:
                print("Census batch failed:", response.stderr.decode(errors="replace"), flush=True)
        if not cached.exists():
            log.append(dict(url=GEOCODER, batch_size=len(segment), input_sha256=digest, status="missing response"))
            continue
        data = cached.read_bytes()
        seen = set()
        outcomes = Counter()
        for row in csv.reader(io.StringIO(data.decode("utf-8-sig"))):
            if len(row) < 3 or row[0] not in index:
                continue
            location, ids = index[row[0]]
            seen.add(row[0])
            outcomes[row[2]] += 1
            if len(row) < 6 or row[2] != "Match" or row[3] != "Exact":
                continue
            if not re.search(rf",\s*{location[2]}\s*,", row[4]):
                continue
            lon, lat = map(float, row[5].split(","))
            for id_ in ids:
                result[id_] = (lat, lon, row[4])
        log.append(dict(url=GEOCODER, benchmark="Public_AR_Current", batch_size=len(segment),
                        responses=len(seen), outcomes=dict(outcomes), input_sha256=digest, retrieval_utc=datetime.fromtimestamp(
                            cached.stat().st_mtime, timezone.utc).date().isoformat(),
                        response_sha256=hashlib.sha256(data).hexdigest(), cache=cached.name,
                        status="retrieved"))
        print(f"Geocoding returned {len(seen)} of {len(segment)} addresses in batch {start//1000+1}", flush=True)
    return result, log


def homepage(value):
    if not value:
        return ""
    website = value.strip()
    if not urlsplit(website).scheme:
        website = "https://" + website
    return website if urlsplit(website).scheme in {"http", "https"} and urlsplit(website).hostname else ""


def h3_outputs(rows, resolution):
    buckets = defaultdict(list)
    for row in rows:
        cell = h3.geo_to_h3(row["latitude"], row["longitude"], resolution)
        buckets[cell].append({k: row[k] for k in ("club_id", "name", "city", "state", "website")})
    features, panels = [], {}
    for cell, clubs in sorted(buckets.items()):
        count = len({r["club_id"] for r in clubs})
        assert count == len(clubs)
        ring = [list(point) for point in h3.h3_to_geo_boundary(cell, geo_json=True)]
        ring.append(ring[0])
        features.append(dict(type="Feature", id=cell, properties=dict(h3=cell, provider_count=count),
                             geometry=dict(type="Polygon", coordinates=[ring])))
        panels[cell] = dict(provider_count=count, clubs=sorted(clubs, key=lambda club:club["name"].casefold()))
    scope = "US Club Soccer listed locations, including offices"
    pilot.dump(f"h3-r{resolution}.geojson", dict(type="FeatureCollection", scope=scope, features=features))
    pilot.dump(f"h3-r{resolution}-panel.json", dict(scope=scope, resolution=resolution, hexes=panels))
    assert sum(p["provider_count"] for p in panels.values()) == len(rows)
    return len(panels)


def city_key(row):
    return " ".join(row["city"].split()).casefold(), row["state"]


def street_key(street, postal):
    tokens = re.findall(r"[a-z0-9]+", street.casefold())
    suffixes = {"avenue":"ave", "boulevard":"blvd", "court":"ct", "drive":"dr",
                "lane":"ln", "parkway":"pkwy", "place":"pl", "road":"rd", "street":"st",
                "terrace":"ter", "circle":"cir"}
    tokens[-1] = suffixes.get(tokens[-1], tokens[-1])
    return " ".join(tokens), postal


def city_audit(listings, mapped, matches):
    counts = Counter(city_key(row) for row in mapped if row["city"].strip())
    top = sorted(counts, key=lambda key: (-counts[key], key))[:3]
    mapped_by_id = {row["club_id"]: row for row in mapped}
    result = []
    for key in top:
        raw = [row for row in listings if city_key(row) == key]
        distinct = {row["id"]: row for row in raw}
        shown = [row for id_, row in distinct.items() if id_ in mapped_by_id]
        street_groups, coordinate_groups = defaultdict(list), defaultdict(list)
        for row in distinct.values():
            parts = address(row)
            if parts:
                street, _, _, postal = parts
                street_groups[street_key(street, postal)].append(row["id"])
        for row in shown:
            point = mapped_by_id[row["id"]]
            coordinate_groups[point["latitude"], point["longitude"]].append(row["id"])
        names = Counter(" ".join(row["name"].split()).casefold() for row in distinct.values())
        result.append(dict(city=key[0].title(), state=key[1], raw_listings=len(raw),
                           distinct_directory_ids=len(distinct), mapped_clubs=len(shown),
                           records_with_street=sum(map(len, street_groups.values())),
                           distinct_streets=len(street_groups),
                           repeated_street_club_ids=[ids for ids in street_groups.values() if len(ids)>1],
                           distinct_matched_addresses=len({matches[row["id"]][2] for row in shown}),
                           repeated_coordinates=[
                               dict(club_ids=ids, same_exact_address=len({matches[id_][2] for id_ in ids})==1)
                               for ids in coordinate_groups.values() if len(ids)>1],
                           repeated_club_names=[name for name, count in names.items() if count>1],
                           city_variants=dict(Counter(row["city"] for row in raw)),
                           sources=sorted({row["source_url"] for row in raw}),
                           records=[dict(club_id=row["id"], name=row["name"], city=row["city"],
                                         mapped=row["id"] in mapped_by_id, source_url=row["source_url"])
                                    for row in raw]))
    return result


def main(fetch):
    OUT.mkdir(exist_ok=True, parents=True)
    pilot.OUT = OUT
    raw, qa, listings = pages()
    candidates = [c for c in raw.values() if eligibility(c)]
    matches, log = geocodes(candidates, fetch)
    clean = []
    for club in candidates:
        match = matches.get(club["id"])
        status = "mapped" if match else "unmatched street address" if address(club) else "missing usable street address"
        clean.append(dict(club_id=club["id"], name=club["name"], city=club["city"], state=club["state"],
                          website=homepage(club["website_url"]), team_count=club["team_count"], status=status,
                          latitude=match[0] if match else "", longitude=match[1] if match else "",
                          geocoding_precision="TIGER street interpolation" if match else "",
                          source_url=club["source_url"], retrieved_utc=club["retrieved_utc"]))
    mapped = [r for r in clean if r["status"] == "mapped"]
    assert mapped, "No address matches cached. Run with --geocode."
    totals = {r["code"]: r["count"] for r in json.loads((CACHE / "nat-usclub-states").read_text())}
    coverage = []
    for state in sorted(STATES):
        statuses = Counter(r["status"] for r in clean if r["state"] == state)
        coverage.append(dict(state=state, directory_advertised=totals.get(state, ""),
                             directory_ids_retrieved=sum(r["state"] == state for r in raw.values()),
                             selected_clubs=sum(statuses.values()), mapped=statuses["mapped"],
                             submitted=sum(c["state"] == state and bool(address(c)) for c in candidates),
                             unmatched=statuses["unmatched street address"],
                             missing_street=statuses["missing usable street address"]))
    pilot.table("clubs.csv", clean)
    pilot.dump("city-audit.json", city_audit(listings, mapped, matches))
    pilot.table("state-coverage.csv", coverage)
    pilot.dump("geocoding-manifest.json", log)
    subset = [r for r in mapped if r["state"] == "CO" and 39.86 < r["latitude"] < 40.12
              and -105.34 < r["longitude"] < -104.99]
    cells = {r: h3_outputs(mapped if r != 6 else subset, r) for r in (3, 4, 5, 6)}
    qa.update(selected_clubs=len(clean), mapped_clubs=len(mapped),
              submitted_clubs=sum(bool(address(c)) for c in candidates),
              missing_street=sum(not address(c) for c in candidates),
              unmatched_clubs=sum(bool(address(c)) for c in candidates) - len(mapped),
              mapped_states=sum(r["mapped"] > 0 for r in coverage if r["state"] != "DC"),
              mapped_dc=any(r["mapped"] > 0 for r in coverage if r["state"] == "DC"),
              mapped_boulder_inset=len(subset), cells=cells)
    pilot.dump("qa.json", qa)
    print(json.dumps(qa, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geocode", action="store_true")
    main(parser.parse_args().geocode)
