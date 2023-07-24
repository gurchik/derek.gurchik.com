#!/usr/bin/env python3

import http.server
import socketserver
import os.path

address = ("0.0.0.0", 8080)

BUILD_DIR = "./build"


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
        """
        # No need to do anything for /, the server already serves index.html
        # If the requested path doesn't have .html, but the file exists with the
        # .html suffix, then rewrite to serve that
        if path != "/" and not path.endswith(".html"):
            if os.path.isfile(BUILD_DIR + path + ".html"):
                path += ".html"

        return super().translate_path(path)


with socketserver.TCPServer(address, Handler) as httpd:
    print(f"Serving at {address}")
    httpd.serve_forever()
