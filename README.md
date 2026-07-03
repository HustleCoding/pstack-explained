# pstack-explained

An unofficial, interactive reading aid for **pstack**, [poteto's](https://x.com/poteto) set of engineering skills for coding agents.

A single self-contained HTML page (`index.html`) that explains pstack's playbooks, skills, and principles, with a live playbook router that mirrors how `/poteto-mode` matches a task to a playbook. No build step, no dependencies.

## Live site

https://hustlecoding.github.io/pstack-explained/

## How it deploys

GitHub Pages, served by a GitHub Actions workflow in [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml). Every push to `master` publishes the repository root as the Pages site. The Pages source is set to **GitHub Actions** (not a branch), so the workflow owns the deployment.

## Local preview

Open `index.html` in any browser.

## Contents

`index.html` is the whole app. Markup, styles, data, and router logic live inline.

`.github/workflows/deploy.yml` is the GitHub Pages deployment workflow.

## Notes

This page mirrors the pstack skills installed on the author's machine, not a live install. pstack itself ships as a plugin via `/add-plugin pstack`; this repository is an independent explanatory tool, not affiliated with pstack.
