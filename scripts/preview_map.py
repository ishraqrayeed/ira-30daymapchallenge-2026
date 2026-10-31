"""Serve a map on localhost so browser tile requests have an HTTP referrer."""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import webbrowser

ROOT = Path(__file__).resolve().parents[1]


class PreviewHandler(SimpleHTTPRequestHandler):
    """Give the page an explicit browser referrer policy for external tiles."""

    def end_headers(self):
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        super().end_headers()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--directory", type=Path, default=ROOT / "maps/day01-points")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    directory = args.directory.resolve()
    if not (directory / "map.html").is_file():
        parser.error(f"No map.html in {directory}; generate the interactive map first")
    handler = partial(PreviewHandler, directory=str(directory))
    try:
        server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
    except OSError as exc:
        parser.exit(1, f"Cannot start local preview: {exc}. Try a different --port.\n")
    with server:
        url = f"http://127.0.0.1:{server.server_port}/map.html"
        print(f"Map preview: {url}\nPress Ctrl+C to stop.", flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
