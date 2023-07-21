#!/usr/bin/env python3

from livereload import Server, shell

build = shell("./build.py")

build()

server = Server()
server.watch("content/**/*", build)
server.watch("theme/**/*", build)
server.serve(root="build/")
