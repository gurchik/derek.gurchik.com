# derek.gurchik.com

## Development setup

* `virtualenv venv/`
* `source venv/bin/activate`
* `pip install -r requirements.txt`
* `./serve.py`

## Cloudflare setup

Follow [these instructions](https://developers.cloudflare.com/pages/framework-guides/deploy-anything/) to set up a custom deployment pipeline for Cloudflare Pages.

* Build command: `./build.py`
* Build output directory: `build/`

The Python version can be specified by configuring the `PYTHON_VERSION` environment variable in the project settings, or by creating a `.python-version` file in the root of the project. Dependencies listed in `requirements.txt` will automatically be installed prior to running the build command.

Note the `_redirects` file, see more details [here](https://developers.cloudflare.com/pages/platform/redirects/). It needs to be copied to the build directory.