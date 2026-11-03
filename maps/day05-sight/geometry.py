"""Marking-aligned Opta → metric pitch conversion and goal geometry.

Landmarks follow mplsoccer's published Opta/custom pitch definitions. Independent
piecewise interpolation keeps the penalty spot and penalty/goal areas aligned.
Source x increases toward the attacking goal; y increases from bottom to top.
"""
from bisect import bisect_right
from math import acos, degrees, hypot

OPTA_X = (0, 5.8, 11.5, 17, 50, 83, 88.5, 94.2, 100)
METRIC_X = (0, 5.5, 11, 16.5, 52.5, 88.5, 94, 99.5, 105)
OPTA_Y = (0, 21.1, 36.8, 45.2, 54.8, 63.2, 78.9, 100)
METRIC_Y = (0, 13.84, 24.84, 30.34, 37.66, 43.16, 54.16, 68)
POSTS = ((105.0, 30.34), (105.0, 37.66))


def interpolate(value, source, target):
    if not source[0] <= value <= source[-1]:
        raise ValueError(f'Coordinate outside pitch: {value}')
    i = min(len(source) - 2, bisect_right(source, value) - 1)
    ratio = (value - source[i]) / (source[i + 1] - source[i])
    return target[i] + ratio * (target[i + 1] - target[i])


def normalize(x, y):
    return interpolate(x, OPTA_X, METRIC_X), interpolate(y, OPTA_Y, METRIC_Y)


def sight_geometry(x, y):
    a, b = [(px - x, py - y) for px, py in POSTS]
    denominator = hypot(*a) * hypot(*b)
    if denominator == 0:
        raise ValueError('Sight angle undefined at a goalpost')
    cosine = max(-1, min(1, (a[0] * b[0] + a[1] * b[1]) / denominator))
    return hypot(105 - x, 34 - y), degrees(acos(cosine))
