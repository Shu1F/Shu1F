# Activity graph

`generate_activity_graph.py` fetches the last 31 days of contributions from the
GitHub GraphQL API and writes `assets/activity-graph.svg` using Python's standard
library. The profile displays this checked-in SVG, so a failed refresh leaves the
last successful graph visible.

Run from the repository root with Python 3 and an authenticated GitHub CLI:

```sh
python3 scripts/generate_activity_graph.py
```

The `Update activity graph` workflow runs daily at 00:17 UTC (09:17 JST), when its
script or workflow changes on `main`, or manually from the Actions tab. It uses
the built-in `GITHUB_TOKEN`; no personal access token or external image service
is required. GitHub Actions must be enabled and allowed to push to `main`.

The graph uses UTC dates and retains the Tokyo Night color palette. Contribution
visibility follows the GitHub API permissions of the token used for generation.
