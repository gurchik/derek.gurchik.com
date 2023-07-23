# derek.gurchik.com

The source code for my site at http://derek.gurchik.com

## Generator

Like countless other people, I've decided to write my own site generator. I used to use all the popular site generators out there like Jekyll, Hugo, etc. Whenever I took a break and returned to the code, I found the intricacies of the framework too hard to remember. Rather than worry about that anymore, I made a very simple generator.

* The files in `static/` are copied directly to the build directory.
* The markdown files in `content/` provide the content.
  * You need to specify a `template` name in the front matter of each file to know which template to use for the file.
  * Their organization within in the build directory matches the organization in the content directory. For example, `content/some/path/to/post.md` will be rendered to `build/some/path/to/post.md`.
* The Jinja templates in `templates/` are used for rendering the content. The templates receive the following Jinja variables:
  * `{{ content }}` - The rendered html of the markdown file
  * `{{ url }}` - The url to the rendered markdown. For example, `content/some/file.md` will have a `url` of `some/file`. No `.html` extension is given due to the intention to deploy to Cloudflare Pages, see below.
  * In addition, any variables specified in the front matter (and defined in `REQUIRED_FRONTMATTER`).

## Development setup

* `virtualenv venv/`
* `source venv/bin/activate`
* `pip install -r requirements.txt`
* `./serve.py`

## Deployment

I deploy to Cloudflare Pages because it's free and it's very easy to use a custom framework. Follow [these instructions](https://developers.cloudflare.com/pages/framework-guides/deploy-anything/) to set it up. All you need to do is specify `./build.py` as the build command and `build/` as the build output directory.

Dependencies listed in `requirements.txt` will automatically be installed prior to running the build command. The Python version can be specified by configuring the `PYTHON_VERSION` environment variable in the project settings, or by creating a `.python-version` file in the root of the project. 

I'm also using a `_redirects` file, see more details [here](https://developers.cloudflare.com/pages/platform/redirects/). Place this file in the `static/` directory and it'll be copied to the build directory automatically.

Cloudflare Pages redirects all requests with a `.html` extension. Therefore, when writing hyperlinks in your built content, your link should remove the `.html` extension to save the client from an unnecessary redirect.

## License

The site generator code (build.py) is licensed under the MIT license.

The overall of the site (contents of the `static/`, `content/`, and `templates/` directories) is licensed under a [Creative Commons Attribution-ShareAlike 4.0 International](http://creativecommons.org/licenses/by-sa/4.0/) license.