"""Validate the 2026 source events, normalize coordinates, and derive geometry."""
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean, median

from fetch_data import CACHE, HERE, ROOT, main as verify_cache
from geometry import normalize, sight_geometry, POSTS

OUTPUT = ROOT / 'data/processed/day05-sight'


def read(name):
    with (CACHE / name).open(newline='') as handle:
        return list(csv.DictReader(handle))


def process():
    verify_cache()
    manifest = json.loads((HERE / 'source-manifest.json').read_text())
    fifa_matches = [m for m in read('fifa_matches.csv')
                    if 'Argentina' in (m['home_team'], m['away_team'])]
    attempts = [s for s in read('fifa_attempts_at_goal.csv') if s['player_name'] == 'Lionel MESSI']
    appearances = [s for s in read('fifa_match_appearances.csv')
                   if s['player_name'] == 'Lionel MESSI' and s['appeared'] == 'True']
    result, audit, assists = [], [], 0
    for item in manifest['files']:
        if item['cache_name'].startswith('fifa_'):
            continue
        rows = read(item['cache_name'])
        meta = rows[0]
        opponent = meta['away_team'] if meta['home_team'] == 'Argentina' else meta['home_team']
        match = next(m for m in fifa_matches if opponent in (m['home_team'], m['away_team']))
        source = [r for r in rows if r.get('player') == 'Lionel Messi'
                  and r.get('isShot') == 'True' and r['period_value'] != '5']
        check = [s for s in attempts if s['match_id'] == match['match_id']]
        assert len(source) == len(check), f'Incomplete shot coverage: {opponent}'
        assert Counter(int(r['minute']) for r in source) == Counter(int(r['minute']) for r in check), opponent
        assert sum(r.get('isGoal') == 'True' for r in source) == sum(r['outcome'] == 'On Target - Goal' for r in check)
        assists += sum(r.get('player') == 'Lionel Messi' and r.get('qual_IntentionalGoalAssist') == 'True' for r in rows)
        for row in source:
            sx, sy = float(row['x']), float(row['y'])
            x, y = normalize(sx, sy)
            distance, angle = sight_geometry(x, y)
            assert 0 <= x <= 105 and 0 <= y <= 68 and 0 < angle <= 180
            goal, penalty = row.get('isGoal') == 'True', row.get('qual_Penalty') == 'True'
            outcome = ('Goal' if goal else 'Blocked' if row.get('qual_Blocked') == 'True'
                       else {'SavedShot': 'Saved / stopped', 'MissedShots': 'Off target',
                             'ShotOnPost': 'Woodwork'}.get(row['event'], row['event']))
            # Keep the actual source clock; FIFA official goal-minute labels can differ.
            minute, second = int(row['minute']), int(float(row['second']))
            result.append(dict(source_event_id=f"{row['match_id']}:{row['eventId']}",
                match=f"{match['home_team']} v {match['away_team']}", opponent=opponent,
                date=datetime.strptime(match['date'], '%d %B %Y').date().isoformat(),
                source_date=row['match_date'], minute=minute, second=second,
                clock=f'{minute:02d}:{second:02d}', period=int(row['period_value']),
                source_x=sx, source_y=sy, shot_x=x, shot_y=y,
                distance_to_goal_m=distance, sight_angle_deg=angle,
                outcome=outcome, source_outcome=row['event'], is_goal=goal,
                is_penalty=penalty, body_part=('Left foot' if row.get('qual_LeftFoot') == 'True'
                    else 'Right foot' if row.get('qual_RightFoot') == 'True'
                    else 'Head' if row.get('qual_Head') == 'True' else ''),
                shot_type='Penalty' if penalty else 'Direct free kick' if row.get('qual_DirectFreekick') == 'True' else 'Other',
                source_url=item['url'], fifa_report_url=match['source_url']))
        audit.append(dict(opponent=opponent, shots=len(source), goals=sum(r.get('isGoal') == 'True' for r in source),
                          fifa_attempts=len(check), minute_multiset_matches=True, fifa_match_id=match['match_id']))
    result.sort(key=lambda r: (r['date'], r['period'], r['minute'], r['second']))
    assert len(result) == len({r['source_event_id'] for r in result})
    assert len(result) == 35 and sum(r['is_goal'] for r in result) == 8
    assert len(appearances) == 8 and assists == 4
    penalties = [r for r in result if r['is_penalty']]
    assert len(penalties) == 2
    assert all(abs(r['distance_to_goal_m'] - 11) < 1e-8 for r in penalties)
    nonpen = [r for r in result if not r['is_penalty']]
    widest = max(nonpen, key=lambda r: r['sight_angle_deg'])
    narrowest = min(nonpen, key=lambda r: r['sight_angle_deg'])
    longest_goal = max((r for r in nonpen if r['is_goal']), key=lambda r: r['distance_to_goal_m'])
    heroes = [dict(event_id=r['source_event_id'], label=label, number=i+1) for i, (r,label) in
              enumerate([(widest, 'Widest view'), (narrowest, 'Narrowest view'), (longest_goal, 'Longest goal')])]
    assert len({h['event_id'] for h in heroes}) == 3
    summary = dict(title='WHAT MESSI SAW', subtitle='Every shot begins with an angle.',
        matches=len(audit), appearances=len(appearances), total_shots=len(result), non_penalty_shots=len(nonpen),
        goals=sum(r['is_goal'] for r in result), assists=assists, goal_involvements=8+assists,
        career_world_cup_goals=13+8, penalties=len(penalties), shootout_shots=0,
        geometry_summary_population='33 non-penalty attempts; both match penalties shown but excluded from summaries',
        median_distance_m=median(r['distance_to_goal_m'] for r in nonpen),
        median_sight_angle_deg=median(r['sight_angle_deg'] for r in nonpen),
        widest=widest, narrowest=narrowest,
        mean_goal_angle_deg=mean(r['sight_angle_deg'] for r in nonpen if r['is_goal']),
        mean_non_goal_angle_deg=mean(r['sight_angle_deg'] for r in nonpen if not r['is_goal']),
        heroes=heroes, pitch_metres=[105,68], goalposts_metres=POSTS,
        source_coordinate_system='Opta 0–100; attack increasing x; increasing y bottom to top',
        conversion='Piecewise linear interpolation between pitch markings, using published mplsoccer Opta/custom landmarks',
        xg_available=False, complete_shot_end_xy_available=False, publication_ready=False,
        publication_hold='Event-data reuse terms require clarification before public distribution',
        match_validation=audit,
        caveats=['Source attempt definition retained, including FIFA referee-event entry.',
                 'Source clock displayed verbatim; it can differ from official goal-minute labels.',
                 'Source SavedShot includes stopped/blocked attempts; outcome is qualified where possible.',
                 'Actual stadium dimensions and defenders, goalkeeper, orientation, and control are not modeled.'])
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with (OUTPUT / 'messi_wc2026_shots.csv').open('w', newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=list(result[0])); writer.writeheader(); writer.writerows(result)
    # Pitch coordinates are local metres, not geographic lon/lat: deliberately no GeoJSON.
    (OUTPUT / 'messi_wc2026_shots.json').write_text(json.dumps(result,indent=2)+'\n')
    (OUTPUT / 'day05_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (HERE / 'analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
    qa = dict(all_35_events_have_coordinates=True, all_8_matches_crosschecked=True,
        all_source_minute_multisets_match_fifa=True, unique_event_ids=True,
        penalties_at_11_metres=True, all_points_in_pitch=True, goal_width_m=7.32,
        penalty_sight_angle_deg=sight_geometry(94,34)[1],
        central_angle_greater_than_wide=sight_geometry(85,34)[1]>sight_geometry(85,55)[1],
        near_angle_greater_than_far=sight_geometry(95,34)[1]>sight_geometry(75,34)[1],
        shots=len(result), goals=summary['goals'], geometry_population=len(nonpen), publication_ready=False,
        processed_csv_sha256=hashlib.sha256((OUTPUT/'messi_wc2026_shots.csv').read_bytes()).hexdigest())
    (HERE / 'map.qa.json').write_text(json.dumps(qa,indent=2)+'\n')
    print(json.dumps({k:summary[k] for k in ['total_shots','goals','median_distance_m','median_sight_angle_deg','heroes']},indent=2))
    return result, summary


if __name__ == '__main__':
    process()
