# Publish on GitHub Pages

Selected account: **ishraqrayeed**.
Selected new public repository: **ira-30daymapchallenge-2026**.

Status: deployment files are prepared and validated locally. This workspace cannot
reach GitHub's API or initialize `.git`, so repository creation, push, and the
initial deployment must run in the user's normal terminal.

## Connect and publish

From the repository directory:

```sh
cd /Users/ishraq.ahmed/Documents/repo/codex_test/30daymapchallenge
gh auth login --hostname github.com --web --git-protocol https --scopes repo,workflow
bash scripts/publish_github.sh
```

Sign in as `ishraqrayeed` in the browser. If already authenticated to that account,
the login command can be skipped. The publish script verifies the active account,
builds the site, runs checks, initializes Git on `main`, commits the intended
project paths, creates the public repository, pushes, configures Pages, and
starts the deployment workflow. It does not force-push or store tokens in the repo.

The script uses your existing Git identity if configured; otherwise it sets a
repository-local username and GitHub noreply email. It stops if an existing origin
points elsewhere. Raw caches remain ignored and are not part of the site artifact.

After deployment succeeds, the expected URLs are:

- Repository: https://github.com/ishraqrayeed/ira-30daymapchallenge-2026
- Site root: https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/
- Day 1: https://ishraqrayeed.github.io/ira-30daymapchallenge-2026/day01-points/

These are intended addresses, not a claim that deployment has already completed.

## Site packaging

`scripts/build_pages.py` checks the generated map against its QA count and copies
the HTML and reports to `_site`. The root is now a portfolio index linking to
Day 1 at `/day01-points/`. The previous `/day01/` address redirects to that map.
The HTML embeds the selected public event data and requests JavaScript and OSM
tiles in the reader's browser. No Python backend or geospatial installs are
required on the Pages deployment runner.

`.github/workflows/pages.yml` uses the official checkout, configure-pages,
upload-pages-artifact, and deploy-pages actions. Publication is manually triggered,
so edits pushed later do not publish until the workflow is run again.

## Later updates

Regenerate the map, review it locally, then run `bash scripts/publish_github.sh`
again. It reuses the selected repository and dispatches a fresh deployment.

## Final live check

After the workflow succeeds, open the public URL and verify the basemap, mode
filter, Denver-time tooltips, attribution, and narrow-screen layout before taking
the LinkedIn screenshot. Neither live browser verification nor social posting has
been performed by this setup step.

References:
- [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages)
- [Custom Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)

## Routing update

The initial site opened Day 1 at the root. The revised build separates the portfolio
index from the Day 1 map. Publish again to apply this change to the live site.
