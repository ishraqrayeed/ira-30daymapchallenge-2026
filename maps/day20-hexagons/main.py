"""Build the Day 20 evaluation from cached directory data and reviewed evidence."""
import csv
import html
import json
import re
from collections import Counter, defaultdict

import h3

from download_data import CACHE, HERE

OUT = HERE / "outputs"
SOURCES = {}


def tsv(name):
    with (HERE / name).open() as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    if any(None in row or None in row.values() for row in rows):
        raise ValueError(f"Malformed TSV row in {name}")
    return rows


def read(key):
    return (CACHE / key).read_text()


def dump(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def table(name, rows):
    with (OUT / name).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def source_fields(key):
    row = SOURCES[key]
    return dict(source_url=row["url"], retrieved_utc=row["retrieved_utc"])


def geocode(venue):
    key = venue["coordinate_source"]
    expected = venue["match_prefix"].casefold()
    if key.startswith("geo-"):
        candidates = json.loads(read(key))["result"]["addressMatches"]
        for match in candidates:
            if match["matchedAddress"].casefold().startswith(expected):
                point = match["coordinates"]
                return point["y"], point["x"], match["matchedAddress"], venue["precision"]
    elif key.startswith("esri-"):
        for match in json.loads(read(key))["candidates"]:
            if (match["address"].casefold().startswith(expected)
                    and match["attributes"]["Addr_type"] in
                    {"PointAddress", "StreetAddress", "StreetAddressExt", "Subaddress"}):
                point = match["location"]
                return point["y"], point["x"], match["address"], match["attributes"]["Addr_type"]
    else:
        marker = re.search(r'value="([^"]+)" id="hdn_MapSearchResults"', read(key))
        if marker:
            match, = json.loads(html.unescape(marker[1]))
            if match["Name"].casefold() == expected:
                return float(match["Latitude"]), float(match["Longitude"]), match["Name"], venue["precision"]
    return "", "", "", ""


def clean():
    providers = {p["provider_id"]: p for p in tsv("providers.tsv")}
    venues = {v["venue_id"]: v for v in tsv("venues.tsv")}
    rows, review = [], tsv("review.tsv")
    keys = set()
    for observation in tsv("observations.tsv"):
        provider = providers[observation["provider_id"]]
        venue = venues.get(observation["venue_id"], {})
        ids = observation["evidence"].split(";") + [key for key in
                (venue.get("address_source"), venue.get("coordinate_source")) if key]
        lat, lon, matched, precision = geocode(venue) if venue else ("", "", "", "")
        if lat != "":
            assert 39.8 < lat < 40.2 and -105.5 < lon < -104.9, venue
        status = "verified" if (observation["eligibility"] == observation["venue_link"]
                                == "verified" and lat != "") else "unverified"
        key = tuple(observation[field] for field in ("provider_id", "program_id", "venue_id", "season"))
        assert key not in keys, key
        keys.add(key)
        row = dict(observation, provider_name=provider["provider_name"],
                   original_provider_name=provider["provider_name"],
                   venue_name=venue.get("venue_name", ""), venue_address=venue.get("venue_address", ""),
                   city=venue.get("city", ""), latitude=lat, longitude=lon, geocoding_precision=precision,
                   geocode_match=matched, coordinate_url=SOURCES[venue["coordinate_source"]]["url"] if venue else "",
                   discovery_address=provider["discovery_address"], discovery_city=provider["discovery_city"],
                   discovery_zip=provider["discovery_zip"], zip_centroid="",
                   evidence_urls=" | ".join(SOURCES[ref]["url"] for ref in dict.fromkeys(ids)),
                   evidence_retrieved_utc=" | ".join(sorted({SOURCES[ref]["retrieved_utc"] for ref in ids})),
                   program_url=SOURCES[observation["program_link"]]["url"], verification_status=status)
        rows.append(row)
        if status != "verified":
            issue = "geocoding_failure" if venue and lat == "" else observation["venue_link"]
            review.append(dict(subject="/".join(key[:2]), issue=issue,
                               reason=observation["note"], evidence_urls=row["evidence_urls"]))
    table("pilot.csv", rows)
    table("review.csv", review)
    return rows


def directories():
    raw = []
    totals = {"Play Club Soccer": {"CO": 19, "CA": 203, "FL": 92}, "US Club Soccer": {}}
    def add(group, source, identity, name, city="", state="", address="", zip_code="", website="",
            kind="provider", hint=""):
        raw.append(dict(source_group=group, record_type=kind, record_id=identity, original_name=name,
                        discovery_city=city, discovery_state=state, discovery_address=address,
                        discovery_zip=zip_code, website=website, hint=hint, **source_fields(source)))

    for row in tsv("play-extract.tsv"):
        add("Play Club Soccer", row["source_id"], row["name"], row["name"], row["city"],
            row["state"], hint=row["league_hint"])
    for key in sorted(SOURCES):
        if not re.fullmatch(r"usclub-[a-z]{2}-\d", key):
            continue
        page = json.loads(read(key))
        totals["US Club Soccer"][key.split("-")[1].upper()] = page["total_records"]
        assert page["records_on_page"] == len(page["clubs"])
        for club in page["clubs"]:
            add("US Club Soccer", key, club["id"], club["name"], club["city"], club["state"],
                " ".join(filter(None, (club["address1"], club["address2"]))), club["zipcode"],
                club["website_url"], hint=f'{club["org_type"]}; {club["team_count"]} teams')
    menus = re.findall(r'<a class="mega-menu-link" href="(https?://[^"]+)">([^<]+)</a>', read("usyouth"))
    # The state-site flyout ends at Wyoming. Keep one record per link.
    names = list(dict.fromkeys((url, name) for url, name in menus))
    start = next(i for i, (_, name) in enumerate(names) if name == "Alabama")
    end = next(i for i, (_, name) in enumerate(names) if name == "Wyoming")
    for url, name in names[start:end + 1]:
        add("US Youth Soccer", "usyouth", name, html.unescape(name), website=url, kind="association")
    payload = re.search(r'class="json-LocationInformation" value="([^"]+)', read("ayso"))
    for item in json.loads(html.unescape(payload[1])):
        parts = re.split(r'</BR>', item["Address"] or "", flags=re.I)
        city_state_zip = re.fullmatch(r"(.+?)\s+([A-Z]{2})\s+(\d{5}(?:-\d{4})?)", parts[-1].strip())
        city, state, postal = city_state_zip.groups() if city_state_zip else ("", "", "")
        add("AYSO", "ayso", item["SiteURL"] or item["RowNumber"], item["LocationName"],
            city, state, parts[0] if len(parts) > 1 else "", postal, item["SiteURL"] or "",
            kind="region locator listing")
    table("directory-records.csv", raw)
    summary = {}
    for group in dict.fromkeys(row["source_group"] for row in raw):
        members = [row for row in raw if row["source_group"] == group]
        summary[group] = dict(records=len(members),
                              provider_proxy_keys=(len({row["website"] for row in members if row["website"]})
                                                   if group == "AYSO" else
                                                   len({row["record_id"] for row in members if row["record_type"] == "provider"})),
                              unique_record_keys=len({row["record_id"] for row in members}),
                              geography=dict(sorted(Counter(row["discovery_state"] or "unparsed"
                                                             for row in members).items())),
                              advertised_totals=totals.get(group, {}),
                              verified_programs=0, verified_pairs=0, exclusive_pairs=0)
    summary["CSA maps"] = dict(records=0, provider_proxy_keys=0, verified_programs=0,
                               verified_pairs=0, exclusive_pairs=0)
    return summary


def aggregate(verified, resolution):
    cells = {}
    for row in verified:
        cell = h3.geo_to_h3(row["latitude"], row["longitude"], resolution)
        providers = cells.setdefault(cell, {})
        programs = providers.setdefault(row["provider_id"], dict(provider_id=row["provider_id"],
                            name=row["provider_name"], programs={}))["programs"]
        key = row["program_id"] + "/" + row["season"]
        program = programs.setdefault(key, {field: row[field] for field in (
            "program_id", "program_name", "program_type", "season", "published_age", "normalized_age",
            "program_url", "registration_status")})
        program.setdefault("venues", []).append({field: row[field] for field in (
            "venue_id", "venue_name", "venue_address", "latitude", "longitude", "evidence_urls")})
    panel, features = {}, []
    for cell, providers in sorted(cells.items()):
        for provider in providers.values():
            provider["programs"] = list(provider["programs"].values())
        count = len(providers)
        panel[cell] = dict(provider_count=count, providers=list(providers.values()))
        assert count == len({provider["provider_id"] for provider in panel[cell]["providers"]})
        boundary = [list(point) for point in h3.h3_to_geo_boundary(cell, geo_json=True)]
        if boundary[0] != boundary[-1]:
            boundary.append(boundary[0])
        features.append(dict(type="Feature", id=cell, properties=dict(h3=cell, provider_count=count),
                             geometry=dict(type="Polygon", coordinates=[boundary])))
    scope = "Verified Colorado pilot sample; Boulder, Broomfield and Lafayette postal addresses"
    dump(f"h3-r{resolution}-panel.json", dict(scope=scope, resolution=resolution, hexes=panel))
    dump(f"h3-r{resolution}.geojson", dict(type="FeatureCollection", scope=scope, features=features))
    assert sum(len(program["venues"]) for hexagon in panel.values() for provider in hexagon["providers"]
               for program in provider["programs"]) == len(verified)
    return features


def preview(features, rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    from math import cos, radians

    ivory, ink = "#f6f1e5", "#193b31"
    fig, ax = plt.subplots(figsize=(7.6, 5.3), facecolor=ivory)
    ax.set_facecolor(ivory)
    for feature in features:
        count = feature["properties"]["provider_count"]
        coordinates = feature["geometry"]["coordinates"][0]
        colors = ["#dce7ce", "#a7c59c", "#74a879", "#3e7b61"]
        ax.add_patch(Polygon(coordinates, facecolor=colors[min(count, 4)-1], edgecolor="#809783",
                             linewidth=.8))
        lon, lat = list(zip(*coordinates[:-1]))
        ax.text(sum(lon)/len(lon), sum(lat)/len(lat), str(count), fontsize=14,
                ha="center", va="center", color=ink, weight="bold", zorder=4)
    points = {(r["longitude"], r["latitude"]) for r in rows}
    ax.scatter(*zip(*points), s=15, c=ink, edgecolors=ivory, linewidths=.65, zorder=3)
    for name, x, y in [("Boulder", -105.29, 40.015), ("Lafayette", -105.092, 40.010),
                       ("Broomfield", -105.056, 39.908)]:
        ax.text(x, y, name, fontsize=9, color=ink, ha="center", zorder=5,
                bbox=dict(facecolor=ivory, edgecolor="none", alpha=.86, pad=1.2))
    ax.autoscale()
    ax.margins(.07)
    ax.set_aspect(1 / cos(radians(40)))
    ax.axis("off")
    fig.subplots_adjust(left=.045, right=.955, top=.81, bottom=.13)
    fig.text(.075, .91, "Where America Learns to Play", fontfamily="serif", fontsize=24, color=ink)
    fig.text(.077, .858, "Verified under-10 soccer opportunities · Colorado pilot sample · Fall 2026",
             fontsize=9, color=ink)
    fig.text(.077, .068, "Hex label = distinct providers   •   Dot = verified venue",
             fontsize=9, color=ink)
    fig.text(.077, .033, "Sources: provider schedules, Colorado Soccer Association and city recreation guides",
             fontsize=7, color=ink)
    output = OUT / "pilot-preview.svg"
    fig.savefig(output, metadata={"Date": None})
    output.write_text("\n".join(line.rstrip() for line in output.read_text().splitlines()) + "\n")
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    SOURCES.update({row["id"]: row for row in json.loads((HERE / "source-manifest.json").read_text())})
    rows = clean()
    summary = directories()
    verified = [row for row in rows if row["verification_status"] == "verified"]
    for group in sorted({group for row in rows for group in row["source_group"].split(";")}):
        subset = [row for row in rows if group in row["source_group"].split(";")]
        pairs = [row for row in subset if row["verification_status"] == "verified"]
        summary[group] = dict(records=len(subset), unique_providers=len({r["provider_id"] for r in subset}),
                              verified_programs=len({(r["program_id"], r["season"]) for r in subset
                                                     if r["eligibility"] == "verified"}),
                              verified_pairs=len(pairs),
                              exclusive_pairs=sum(r["source_group"] == group for r in pairs))
    known = {row["provider_id"]: {} for row in tsv("providers.tsv")}
    for row in tsv("coverage.tsv"):
        keys = known if row["provider_id"] == "all" else [row["provider_id"]]
        for key in keys:
            known[key][row["source"]] = row["result"]
    dump("known-provider-coverage.json", known)
    counts = {}
    for resolution in (4, 5, 6):
        features = aggregate(verified, resolution)
        counts[resolution] = len(features)
    preview(features, verified)
    qa = dict(table_rows=len(rows), mapped_pairs=len(verified),
              geocoding_failures=sum(bool(row["venue_id"]) and row["latitude"] == "" for row in rows),
              unmapped_rows=len(rows)-len(verified),
              distinct_mapped_providers=len({r["provider_id"] for r in verified}),
              distinct_mapped_venues=len({r["venue_id"] for r in verified}),
              distinct_mapped_programs=len({(r["provider_id"], r["program_id"], r["season"]) for r in verified}),
              pairs_by_venue_city=dict(Counter(r["city"] for r in verified)), cells=counts, sources=summary)
    dump("qa.json", qa)
    print(json.dumps({k: v for k, v in qa.items() if k != "sources"}, indent=2))


if __name__ == "__main__":
    main()
