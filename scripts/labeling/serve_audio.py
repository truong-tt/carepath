from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class CorsStaticHandler(SimpleHTTPRequestHandler):
    extensions_map = {
        **SimpleHTTPRequestHandler.extensions_map,
        ".aac": "audio/aac",
        ".flac": "audio/flac",
        ".m4a": "audio/mp4",
        ".mp3": "audio/mpeg",
        ".oga": "audio/ogg",
        ".ogg": "audio/ogg",
        ".opus": "audio/ogg",
        ".wav": "audio/wav",
        ".webm": "audio/webm",
    }

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Range, Content-Type")
        super().end_headers()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve local audio files for Label Studio.")
    parser.add_argument("--dir", required=True, type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    audio_dir = args.dir.resolve()
    if not audio_dir.exists():
        raise SystemExit(f"Audio folder not found: {audio_dir}")

    handler = partial(CorsStaticHandler, directory=str(audio_dir))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    url = f"http://{args.host}:{args.port}/"
    print(f"Serving {audio_dir}")
    print(f"Audio URL base: {url}")
    print("Keep this window open while labeling. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped audio server.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
