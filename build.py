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
THEME_DIR = "theme/"
MARKDOWN_EXTENSIONS = [
    # https://python-markdown.github.io/extensions/
    "fenced_code",
    "footnotes",
    "tables",
    # There are a lot more at https://facelessuser.github.io/pymdown-extensions/
    # but I'm choosing to not install that right now.
]
CONTENT = {}
REQUIRED_FRONTMATTER = {
    "pages": ["title"],
    "posts": ["title", "date"],
    "index": ["title"],
}

jinja_loader = FileSystemLoader(THEME_DIR)
jinja = Environment(loader=jinja_loader, autoescape=False)


class MissingFrontmatter(Exception):
    pass


def collect_files(dir):
    ret = []
    for root, _, files in os.walk(dir):
        for file in files:
            ret.append(os.path.join(root, file))
    return ret


def prepare_build_dir():
    if os.path.exists(BUILD_DIR):
        shutil.rmtree(BUILD_DIR, ignore_errors=True)
    os.mkdir(BUILD_DIR)


def create_parent_dirs(path):
    parent_dir = os.path.dirname(path)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)


def build_content(template, content, global_vars):
    dest = content["href"][1:]  # won't work properly with the leading slash
    build_path = os.path.join(BUILD_DIR, dest)
    print(f"Building {build_path}")

    jinja_vars = {**global_vars, **content}

    try:
        html = template.render(**jinja_vars)
        create_parent_dirs(build_path)  # Can't write file unless its directory exists
        with open(build_path + ".html", "w") as f:
            f.write(html)
    except Exception as e:
        print(f"ERROR: Failed to build {build_path}: {e}")


def get_built_path(parent_dir, src_path, custom_extension=None):
    """Get the path for the src file relative to the build directory. The file
    organization will mirror your organization within the parent directory.

    Examples:
    theme/assets/style.css => assets/style.css
    content/assets/images/foo.jpg => assets/images/foo.jpg
    """
    dest = Path(src_path.replace(parent_dir, ""))
    if custom_extension is not None:
        return str(dest.with_suffix(custom_extension))
    return str(dest)


def load_content_files(content_type):
    dir = os.path.join(CONTENT_DIR, content_type)
    contents = []

    for file in collect_files(dir):
        loaded = frontmatter.load(file)
        front_matter = loaded.metadata

        # Remove the file extension from links to built content, matching Cloudflare
        href = get_built_path(dir, file, custom_extension="")

        content = {
            "source": file,
            "href": href,
            "content": markdown.markdown(
                loaded.content, extensions=MARKDOWN_EXTENSIONS
            ),
        }

        frontmatter_fields = REQUIRED_FRONTMATTER[content_type]
        for field in frontmatter_fields:
            if field not in front_matter:
                raise MissingFrontmatter(
                    f"Failed to load {file}: missing required frontmatter field {field}"
                )
            content[field] = front_matter[field]

        contents.append(content)
        print(f"Loaded content {file}")

    CONTENT[content_type] = contents


def copy_file(src, dest):
    create_parent_dirs(dest)  # Can't copy unless its dir exists
    shutil.copy(src, dest)


def copy_assets(dirs):
    for dir in dirs:
        asset_dir = os.path.join(dir, "assets/")
        print(f"Copying assets from {asset_dir}")
        for asset in collect_files(asset_dir):
            built_path = get_built_path(dir, asset)
            dest = os.path.join(BUILD_DIR, built_path)
            copy_file(asset, dest)


def build():
    prepare_build_dir()

    # First, load the content in memory. We can't render any content until all of it
    # has been loaded because we need them to populate the global variables.
    load_content_files("index")
    load_content_files("pages")
    load_content_files("posts")

    # Next, it's helpful to sort the content so we can show them in order
    CONTENT["posts"].sort(key=lambda post: post["date"])

    global_vars = {**CONTENT}

    # Copy the assets
    copy_assets([CONTENT_DIR, THEME_DIR])

    # Render all the content
    for content_type in ["index", "pages", "posts"]:
        template = jinja.get_template(f"{content_type}.html.j2")
        for content in CONTENT[content_type]:
            build_content(template, content, global_vars)

    # Copy misc Cloudflare files
    src = "_redirects"
    dest = os.path.join(BUILD_DIR, src)
    print(f"Copying {dest}")
    copy_file(src, dest)

    print("Build finished")


if __name__ == "__main__":
    build()
