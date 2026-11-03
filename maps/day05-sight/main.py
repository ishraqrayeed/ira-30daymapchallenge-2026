"""Rebuild the local data audit and static-first HTML from pinned source caches."""
from process_shots import process
from render import render

if __name__ == '__main__':
    process()
    render()
