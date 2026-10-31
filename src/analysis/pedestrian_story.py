"""A story subset of fatal crash events involving pedestrians."""

import geopandas as gpd

from src.analysis.crashes import DETAIL_COLUMNS


def select_story_crashes(points: gpd.GeoDataFrame, analysis_qa: dict) -> tuple[gpd.GeoDataFrame, dict]:
    """Select events, without asserting which person died or counting victims."""
    story = points[(points.fatal == 1) & (points.pedestrian == 1)].copy()
    if story.empty:
        raise ValueError("No validated fatal crashes involving pedestrians in this snapshot")
    qa = dict(analysis_qa)
    qa['edition'] = 'Someone Was Walking Here'
    qa['scope'] = 'Fatal crashes involving pedestrians'
    qa['counted_unit'] = 'Unique crash event, not an individual pedestrian death'
    qa['analysis_mapped_incidents'] = analysis_qa['mapped_incidents']
    qa['excluded_from_story_scope'] = len(points) - len(story)
    qa['mapped_incidents'] = len(story)
    qa['fatal_crashes'] = len(story)
    qa['serious_injury_only_crashes'] = 0
    qa['pedestrian_involved_crashes'] = len(story)
    qa['bicycle_involved_crashes'] = int(story.bicycle.sum())
    qa['both_modes_crashes'] = int(story.bicycle.sum())
    qa['annual_counts'] = [
        {'year': row['year'], 'mapped_incidents': int((story.year == row['year']).sum()),
         'fatal_crashes': int((story.year == row['year']).sum()), 'serious_injury_only_crashes': 0}
        for row in analysis_qa['annual_counts']]
    qa['detail_coverage'] = {
        column: int((~story[column].isin(['Not reported', 'Not in snapshot'])).sum())
        for column in DETAIL_COLUMNS}
    return story, qa
