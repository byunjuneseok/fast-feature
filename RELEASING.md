# Releasing

All nine distributions are released **in lockstep**: they always share one version
and are published together. Releases go to PyPI automatically when a version tag
is pushed, authenticated with [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
(OIDC, no tokens or secrets).

## One-time setup

Trusted Publishing must be configured once per PyPI project. Because the packages
do not exist on PyPI yet, register each as a **pending publisher** at
<https://pypi.org/manage/account/publishing/> with these values:

| Field | Value |
| --- | --- |
| Owner | `byunjuneseok` |
| Repository name | `fast-feature` |
| Workflow name | `release.yml` |
| Environment name | `pypi` |

Create one pending publisher for **each** PyPI project name:

- `fast-feature`
- `fast-feature-core`
- `fast-feature-engine`
- `fast-feature-ofrep`
- `fast-feature-testing`
- `fast-feature-storage-inmemory`
- `fast-feature-storage-sqlalchemy`
- `fast-feature-storage-postgresql`
- `fast-feature-admin`

Then create a GitHub Environment named `pypi`
(Settings → Environments → New environment). Optionally add protection rules
(e.g. required reviewers) to gate publishing.

## Cutting a release

1. Set the new version across the workspace and relock:

   ```bash
   uv run python scripts/set_version.py 0.0.1   # use the target version
   uv lock
   ```

   This updates every `[project].version` and pins each first-party dependency to
   `==<version>`, keeping the release coherent.

2. Open a PR with the version bump, let CI pass, and squash-merge to `main`.

3. Tag the merge commit and push the tag:

   ```bash
   git tag v0.0.1
   git push origin v0.0.1
   ```

The `Release` workflow then runs the test gate and, on success, builds and
publishes all nine distributions to PyPI. The tag version must match the version
set in the packages.

## Notes

- Versions are **immutable on PyPI**: a published version cannot be replaced. Bump
  the version for any re-release.
- To rehearse against TestPyPI, add `--publish-url https://test.pypi.org/legacy/`
  to the publish step (and configure pending publishers on TestPyPI).
