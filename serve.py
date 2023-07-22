#!/usr/bin/env python3

import http.server
import socketserver

address = ("0.0.0.0", 8080)


def is_assets_dir(path):
    return path.startswith("/assets/") or path.startswith("assets/")


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="./build", **kwargs)

    #  This is
    # so our local server matches Cloudflare's practice of removing the .html
    def translate_path(self, path):
        """Translate web requests (without .html) to their path on disk (with .html).

        We want to do this because Cloudflare Pages does this, and it's nice to have a
        local server which does this too so we can identify any incorrect links.

        The server already translates requests to / to index.html, so no need to do
        anything there. We also serve requests to /assets/ as-is without rewriting.
        This is technically not how Cloudflare does it (they check if the requested
        file exists and doesn't have a .html extension and serves it as-is if so) but
        it makes implementation easier for me.
        """
        if path != "/" and not is_assets_dir(path):
            path += ".html"
        return super().translate_path(path)


with socketserver.TCPServer(address, Handler) as httpd:
    print(f"Serving at {address}")
    httpd.serve_forever()
