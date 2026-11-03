"""Build a self-contained static-first local HTML research preview."""
import html
import json
import math
import re
from pathlib import Path

from fetch_data import HERE, ROOT


def render():
    rows = json.loads((ROOT / 'data/processed/day05-sight/messi_wc2026_shots.json').read_text())
    summary = json.loads((HERE / 'analysis.json').read_text())
    heroes = {h['event_id']: h for h in summary['heroes']}
    # Both axes use 10 SVG units/metre; no aspect distortion.
    def xy(x, y):
        return 110 + y * 10, 92 + (105 - x) * 10

    def point(row):
        return xy(row['shot_x'], row['shot_y'])

    def line(x1, y1, x2, y2, cls='pitch-line'):
        return f'<line class="{cls}" x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}"/>'

    posts = [xy(*p) for p in summary['goalposts_metres']]
    shape = ['<rect class="field" x="110" y="92" width="680" height="460"/>',
             '<path class="pitch-line" d="M110 552 V92 H790 V552"/>']
    for depth, width in [(16.5,40.32),(5.5,18.32)]:
        left = 110 + (68-width)/2*10
        shape.append(f'<path class="pitch-line" d="M{left} 92 V{92+depth*10} H{left+width*10} V92"/>')
    # Penalty arc: the portion outside the box, with the true 9.15 m radius.
    arc_dx = math.sqrt(9.15**2-5.5**2)*10
    shape.append(f'<path class="pitch-line" d="M{450-arc_dx} 257 A91.5 91.5 0 0 0 {450+arc_dx} 257"/>')
    shape.append('<circle class="penalty-spot" cx="450" cy="202" r="1.8"/>')
    shape.append('<path class="goal-frame" d="M413.4 92 V72 H486.6 V92"/>')
    shape.append(line(*posts[0],*posts[1],cls='goal-mouth'))
    shape += [f'<circle class="goalpost" cx="{x}" cy="{y}" r="3.4"/>' for x,y in posts]
    shape.append('<path class="goal-dimension" d="M413.4 48 H486.6 M413.4 43 V53 M486.6 43 V53"/>')
    shape.append('<text class="dimension-text" x="450" y="34" text-anchor="middle">7.32 m · TWO POSTS</text>')

    cones, rays, dots = [], [], []
    # Render non-goals before goals so goals are never hidden by another marker.
    for row in sorted(rows,key=lambda r:r['is_goal']):
        x,y = point(row); key=row['source_event_id']; hero=heroes.get(key)
        classes = 'shot goal' if row['is_goal'] else 'shot other'
        if row['is_penalty']: classes += ' penalty'
        if hero: classes += ' hero'
        if hero:
            polygon=' '.join(f'{a:.3f},{b:.3f}' for a,b in [(x,y),*posts])
            cones.append(f'<polygon class="cone cone-{hero["number"]}" points="{polygon}" data-event="{key}"/>')
        rays.append(f'<g class="{classes}" data-event="{key}">' + ''.join(line(x,y,*p,cls='sight-line') for p in posts)+'</g>')
        ring = '<circle class="penalty-ring" r="7"/>' if row['is_penalty'] else ''
        # Two identical penalty coordinates: retain both real points, do not jitter.
        if row['is_penalty']:
            ring = '<circle class="penalty-ring" r="7"/>' if row['opponent']=='Austria' else '<circle class="penalty-ring" r="10"/>'
        title = html.escape(f"{row['opponent']} · recorded {row['clock']} · {row['outcome']} · {row['distance_to_goal_m']:.1f} m · {row['sight_angle_deg']:.1f}°")
        dots.append(f'<g class="{classes} marker" data-event="{key}" tabindex="0" role="button" aria-label="{title}" transform="translate({x:.3f} {y:.3f})">'
                    f'<title>{title}</title><circle class="hit-target" r="12"/>{ring}<circle class="shot-dot" r="{5.5 if row["is_goal"] else 4}"/></g>')

    render_portrait(rows, summary, shape, cones, rays, dots)
    print(f'Rendered {len(rows)} real events; {len(heroes)} annotations')


def render_portrait(rows, summary, shape, cones, rays, dots):
    """Reflow the existing geometry, at equal axis scales, onto the 1620 × 1350 artboard."""
    # Reuse all 35 markers and all 70 rays. Only the display extent changes.
    # 20 pixels/metre versus 14 in V2: a 1.43× isotropic viewport zoom.
    # Goal-centred cross-pitch range y=10.2–57.8 m; visible x=67.45–105 m.
    # The crop gives the furthest shot 45.7 artboard pixels of bottom clearance.
    portrait_shape = shape[2:].copy()
    # The outer visible verticals belong to the penalty area in this tight crop.
    # Quiet only those sides; keep the box's bottom edge and six-yard box intact.
    edge = re.fullmatch(r'<path class="pitch-line" d="M([\d.]+) 92 V([\d.]+) H([\d.]+) V92"/>', portrait_shape[0])
    if not edge:
        raise ValueError('Unexpected pitch outline; review before rendering')
    left, bottom, right = edge.groups()
    portrait_shape[0] = (f'<path class="pitch-line" d="M{left} {bottom} H{right}"/>'
                         f'<path class="pitch-line pitch-outer-vertical" d="M{left} 92 V{bottom} M{right} 92 V{bottom}"/>')
    portrait_shape.insert(0, '<path class="pitch-line" d="M110 92 H790"/>')
    portrait_shape = [s for s in portrait_shape if 'goal-dimension' not in s and 'dimension-text' not in s]
    portrait_dots = [d.replace('r="5.5"', 'r="4.5"').replace('r="4"', 'r="3.2"') for d in dots]
    geometry = ('<defs><clipPath id="pitch-crop"><rect x="-245" y="352" width="1570" height="824"/></clipPath></defs>'
                '<rect class="field" x="-245" y="425" width="1570" height="751"/>'
                '<g clip-path="url(#pitch-crop)"><g transform="translate(-360 241) scale(2)">'
                + ''.join(s for s in portrait_shape if not any(c in s for c in ['class="goal-frame"','class="goal-mouth"','class="goalpost"']))
                + '<g class="cones">'+''.join(cones)+'</g><g class="rays">'+''.join(rays)
                + '</g><g class="goal-foreground">'+''.join(s for s in portrait_shape if any(c in s for c in ['class="goal-frame"','class="goal-mouth"','class="goalpost"']))+'</g><g class="dots">'+''.join(portrait_dots)+'</g></g></g>')
    labels=[]
    lanes={1:(975,580),2:(905,1068),3:(-30,903)}
    for hero in summary['heroes']:
        row=next(r for r in rows if r['source_event_id']==hero['event_id'])
        x=-360+2*(110+row['shot_y']*10)
        y=241+2*(92+(105-row['shot_x'])*10)
        lx,ly=lanes[hero['number']]
        target = {1:(957,y),2:(889,y),3:(250,y)}[hero['number']]
        origin=x-11 if hero['number']==3 else x+11
        caption=hero['label'].upper()
        if hero['label']=='Widest view':
            caption += ' · GOAL'
        elif hero['label']=='Narrowest view':
            assert row['outcome']=='Off target', 'Hero outcome changed: review before rendering'
            caption += ' · OFF TARGET'
        labels.append(f'<g class="annotation" data-event="{row["source_event_id"]}">'
            f'<circle class="hero-ring" cx="{x:.3f}" cy="{y:.3f}" r="11"/>'
            f'<path class="leader" d="M{origin:.3f} {y:.3f} L{target[0]:.3f} {target[1]:.3f}"/>'
            f'<text class="callout-value" x="{lx}" y="{ly}">{row["sight_angle_deg"]:.1f}°</text>'
            f'<text class="callout-label" x="{lx}" y="{ly+34}">{html.escape(caption)}</text>'
            f'<text class="callout-detail" x="{lx}" y="{ly+66}">{html.escape(row["opponent"])} · {row["distance_to_goal_m"]:.1f} m</text></g>')
    payload=json.dumps(dict(shots=rows,summary=summary),separators=(',',':')).replace('<','\\u003c')
    script=(HERE/'interaction-template.js').read_text().replace('@@DATA@@',payload)
    result=(HERE/'template.html').read_text().replace('@@GEOMETRY@@',geometry+''.join(labels))
    result=result.replace('@@SCRIPT@@',script).replace('@@SHOTS@@',str(summary['total_shots']))
    result=result.replace('@@GOALS@@',str(sum(bool(row['is_goal']) for row in rows)))
    assert summary['total_shots']==len(rows) and summary['goals']==sum(bool(row['is_goal']) for row in rows)
    result=result.replace('@@MEDIAN_ANGLE@@',f'{summary["median_sight_angle_deg"]:.1f}')
    result=result.replace('@@MEDIAN_DISTANCE@@',f'{summary["median_distance_m"]:.1f}')
    (HERE/'map.html').write_text(result)


if __name__=='__main__':
    render()
