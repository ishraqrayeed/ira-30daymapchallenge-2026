# Driving Monotony Index audit

The old poster shaded **68.90%** of I-70, including every eight-mile section
with a score of 70 or above. Only **17.91%** scored 83 or above. The old
312-mile figure measured contiguous sections at or above 70. At 83 the
longest old high-scoring run was 80 miles.

All 107 sections had sufficient land-cover and slope coverage in both models.
Coverage below 99.5% in either raster, or a missing prevailing class at a
centerline sample, leaves a segment unscored and breaks a qualifying run.
The audit detected neither a missing-data default nor a normalization error.
Straightness was high for most sections at this scale. The old 2.5 km
neighborhood also concealed changes in land cover, giving the scenic
criterion a median score of 91.67. Equal weighting let these high scores
offset much lower land-cover dominance. Land-cover dominance and scenic
repetition were positively correlated, so the terms are related even though
one measures the surrounding area and the other measures change along the road.

## Score distribution

Percent of the full 848.77-mile corridor. Lower bounds are inclusive.

| Score | Original | Revised |
| --- | ---: | ---: |
| 0–<70 | 31.10% | 57.59% |
| 70–<75 | 13.29% | 17.91% |
| 75–<80 | 25.45% | 13.20% |
| 80–<83 | 12.25% | 4.71% |
| 83–<85 | 6.60% | 0.94% |
| 85–<90 | 6.60% | 5.66% |
| 90–100 | 4.71% | 0.00% |

Section-level medians and interquartile ranges. Each section counts once.

| Component | Original median [Q1–Q3] | Revised median [Q1–Q3] | Revised weight |
| --- | ---: | ---: | ---: |
| Straightness | 94.61 [86.51–98.97] | 94.61 [86.51–98.97] | 15% |
| Flatness | 72.18 [65.07–78.57] | 72.18 [65.07–78.57] | 30% |
| Land-cover dominance | 50.49 [33.91–61.96] | 50.49 [33.91–61.96] | 40% |
| Scenic repetition | 91.67 [81.25–95.83] | 79.17 [66.67–91.67] | 15% |
| Composite | 75.95 [68.87–81.64] | 69.01 [58.07–74.70] | |

Pearson correlations across sections.

| Components | Original | Revised |
| --- | ---: | ---: |
| Straightness / flatness | .152 | .152 |
| Straightness / dominance | .181 | .181 |
| Straightness / scenic repetition | .300 | .202 |
| Flatness / dominance | .431 | .431 |
| Flatness / scenic repetition | .275 | .255 |
| Dominance / scenic repetition | .611 | .670 |

## Threshold sensitivity

The minimum run is 15 miles. With eight-mile sections this normally requires
at least two contiguous qualifying sections. Scores are not ranked or
rescaled to a target percentage.

| Threshold | Original miles highlighted with minimum | Revised miles above threshold before minimum | Revised miles highlighted with minimum | Revised longest eligible run |
| --- | ---: | ---: | ---: | ---: |
| 75 | 53.72% | 24.51% | 21.68% | 104 mi, journey miles 600–704 |
| 80 | 26.39% | 11.31% | 9.43% | 80 mi, journey miles 600–680 |
| 85 | 11.31% | 5.66% | 2.83% | 24 mi, journey miles 640–664 |
| 90 | 1.89% | 0.00% | 0.00% | — |

Use **80** because it makes the high class read as four-fifths of the
fixed physical and categorical score scale. At 80, even perfect straightness,
flatness and scenic repetition require at least 50% landscape dominance.
At 75 that lower bound is 37.5%. At 85 it rises to 62.5%. The minimum filters
out isolated peaks. The revised run begins near Oakley, Kansas, and ends
5.2 route miles east of the Burlington, Colorado, reference point.

## Scenic smoothing sensitivity

The original scenic component uses a 5-by-5 majority neighborhood on a
500 m grid. The revised model uses 3-by-3 (1.5 km), providing a local
landscape sample while retaining more variation than the earlier 2.5 km
neighborhood. Polygon generalization is independent of score smoothing.

| Neighborhood | Revised median DMI | Revised route miles highlighted at 80 | Longest eligible run |
| --- | ---: | ---: | ---: |
| 500 m | 61.81 | 4.71% | 40 mi |
| 1.5 km | 69.01 | 9.43% | 80 mi |
| 2.5 km | 69.72 | 12.25% | 88 mi |
| 4.5 km | 70.57 | 13.20% | 96 mi |

The coarse elevation grid suppresses small terrain changes. Land-cover
transitions measure a proxy for visual variety and contain no sightline or
driver survey observations. Scores and endpoints depend on the stated
sampling scales. The [full diagnostic data](assets/monotony-diagnostics.json)
contain percentile distributions, categories, correlations, and every run
for each weight, threshold, and smoothing combination.


## Tiered display

The revised scores have a median of 69.01, a first quartile of 58.07
and a third quartile of 74.70. The display retains the proposed cutoffs:
55 is near the lower quartile, 70 is near the median, and 85 is above
the 90th percentile (80.33). Display thresholds leave the headline
threshold of 80 and minimum length of 15 miles intact.

| Same-band minimum | Moderate | High | Extreme | Total |
| --- | ---: | ---: | ---: | ---: |
| 8 miles | 16 / 352.8 mi | 13 / 312.0 mi | 4 / 48.0 mi | 33 / 712.8 mi |
| 10 miles | 10 / 304.8 mi | 7 / 264.0 mi | 1 / 24.0 mi | 18 / 592.8 mi |

Each cell in the table is a count of stretches followed by route mileage.
Ten miles filters isolated full-length eight-mile sections, while
retaining all runs of two or more full sections. Band changes and gaps
break runs, and the map leaves those gaps open. Land-cover generalization
affects only the geometry, independent of the scores and length filter.
