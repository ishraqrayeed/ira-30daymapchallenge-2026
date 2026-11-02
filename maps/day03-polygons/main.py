"""Rebuild Day 03 from its locally cached OSM extraction."""
from analyze import main as analyze
from render import main as render
from prepare_context import main as context

if __name__ == '__main__':
    analyze()
    context()
    render()
