#!/usr/bin/env python3

import os
import os.path
import shutil
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import markdown
import frontmatter

BUILD_DIR = "build/"
CONTENT_DIR = "content/"
TEMPLATES_DIR = "templates/"
STATIC_DIR = "static/"
MARKDOWN_EXTENSIONS = [
    # https://python-markdown.github.io/extensions/
    "fenced_code",
    "footnotes",
    "tables",
    # There are a lot more at https://facelessuser.github.io/pymdown-extensions/
    # but I'm choosing to not install that right now.
]
REQUIRED_FRONTMATTER = {
    "index.html.j2": [],
    "page.html.j2": ["title"],
    "post.html.j2": ["title", "date"],
}


class MissingFrontmatter(Exception):
    pass


def create_parent_dirs(path):
    parent_dir = os.path.dirname(path)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)


def copy_file(src, dest):
    create_parent_dirs(dest)  # Can't copy unless its dir exists
    shutil.copy(src, dest)


def collect_files(dir):
    ret = []
    for root, _, files in os.walk(dir):
        for file in files:
            ret.append(os.path.join(root, file))
    return ret


def copy_files_from_dir(src, dest):
    for file in collect_files(src):
        new_path = Path(file.replace(src, dest))  # static/foo.txt --> build/foo.txt
        copy_file(file, new_path)
        print(f"Copied {new_path}")


def parse_content_file(path):
    loaded = frontmatter.load(path)
    front_matter = loaded.metadata
    content = markdown.markdown(loaded.content, extensions=MARKDOWN_EXTENSIONS)
    return front_matter, content


def render_template(template, jinja_vars, dest):
    html = template.render(**jinja_vars)
    create_parent_dirs(dest)  # Can't save unless its dir exists
    with open(dest, "w") as f:
        f.write(html)
    print(f"Saved {dest}")


def load_content_from_dir(dir):
    ret = []

    for file in collect_files(dir):
        front_matter, content = parse_content_file(file)

        if "template" not in front_matter:
            raise MissingFrontmatter(
                f"Failed to load {file}: missing required frontmatter field 'template'"
            )

        for required_field in REQUIRED_FRONTMATTER[front_matter["template"]]:
            if required_field not in front_matter:
                raise MissingFrontmatter(
                    f"Failed to load {file}: missing required frontmatter field '{required_field}'"
                )

        # Remove the file extension from links to built content, matching Cloudflare
        # content/my_page.md => /my_page
        url = str(Path(file.replace(dir, "/")).with_suffix(""))

        ret.append(
            {
                "content": content,
                **front_matter,
                "url": url,
            }
        )

    return ret


if __name__ == "__main__":
    # Prepare the build directory
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
    os.mkdir(BUILD_DIR)

    # Copy static assets
    copy_files_from_dir(STATIC_DIR, BUILD_DIR)

    # Load the content in memory. We can't render any content until all of it has been
    # loaded because we need it to populate the global variables.
    content = load_content_from_dir(CONTENT_DIR)

    global_vars = {
        "posts": [c for c in content if c["template"] == "post.html.j2"],
        "pages": [c for c in content if c["template"] == "page.html.j2"],
    }
    # Sort the content in a way that is most helpful for a template
    # TODO: for building a nav menu, we could sort by a "nav_position" key or similar
    global_vars["posts"].sort(key=lambda post: post["date"])

    # Finally, build each of the loaded content files
    jinja_loader = FileSystemLoader(TEMPLATES_DIR)
    jinja = Environment(loader=jinja_loader, autoescape=False)
    for data in content:
        # /index => build/index.html
        path = os.path.join(BUILD_DIR, data["url"][1:]) + ".html"

        template = jinja.get_template(data["template"])
        jinja_vars = {
            **data,  # e.g. "title", "url", etc.
            **global_vars,  # e.g. "posts", "pages", etc.
        }
        render_template(template, jinja_vars, path)

    print("Build finished")
