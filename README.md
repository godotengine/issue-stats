# Godot GitHub issue statistics

This repository gathers hardware and software information reported by users on the
[issue tracker of the main Godot repository](https://github.com/godotengine/godot/issues).
This information is then displayed on a [website](https://godotengine.github.io/issue-stats/).

As such, these statistics are <em>not</em> representative of the entire Godot community,
but they allow seeing what kind of hardware and software is popular among issue reporters.

## How it works

### Backend

- Using GitHub's GraphQL API, 30 requests are performed to fetch the
  description, author and creation date of the 3,000 latest issues.
- In the resulting data, the `System information` field of the issue is parsed
  in a case-sensitive, punctuation-insensitive manner.
  - The operating system, CPU and GPU is detected using this information
    provided by the user. All other information (such as the number of physical
    cores or amount of video memory) is inferred from the model names reported
    by the user.[^1]
  - If there's no valid `System information` section or it contains no usable
    information, the issue is ignored.
- A dictionary of `set()` values is created with all possible values that users
  may be counted in. Each detected value is added to a set of users who have
  reported this information. This ensures that a user may only increment each
  statistic once, even if they've reported several issues with the same hardware
  and software configuration. If a single user has reported several issues with
  *different* hardware and software configurations, then all configurations are
  counted from this user.
- The dictionary is written to a JSON file, with the `set()` value replaced by
  the number of users who have been detected to be using the hardware/software
  in question.
- The resulting JSON file + the frontend is deployed to GitHub Pages using
  GitHub Actions every day.

[^1]: In rare scenarios, this can be inaccurate. In this case, the script errs
    on the side of the most popular variant. For instance, the GeForce GTX 1060
    is considered to always have 6 GB of VRAM, even though it also exists in a
    less popular 3 GB variant. See comments in [`build.py`](/build.py)'s
    hardware detection routine for details.

### Frontend

- The frontend is a single [`index.html`](/index.html) page, plus the
  third-party dependencies mentioned below. No frontend building is required.
- [Frappe Charts](https://frappe.io/charts) is used to display charts.
- [Ky](https://github.com/sindresorhus/ky) is used to make an HTTP request to the JSON file.
- [Water.css](https://watercss.kognise.dev/) is used for styling the page.

## Development

Follow these instructions to set up this site locally for development purposes:

- Make sure you have [Python](https://python.org) 3.7 or later, pip and virtualenv.
- Create a virtualenv and activate it: `virtualenv venv && . venv/bin/activate`.
- Within the virtualenv, install dependencies by running `pip install -r requirements.txt`.
- Copy [`.env.example`](/.env.example) to `.env` and fill in the GitHub API key
  with a personal access token. You can generate one
  [here](https://github.com/settings/tokens) (it **must** have the `public_repo` scope).
- Run `python build.py` to fetch issue data from the GitHub API.
- Start a local web server in the root directory then browse `index.html`.

## License

Copyright © 2023-present Hugo Locurcio and contributors

Unless otherwise specified, files in this repository are licensed under the
MIT license. See [LICENSE.md](LICENSE.md) for more information.
