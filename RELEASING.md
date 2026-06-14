# Releasing

All nine distributions are released **in lockstep**: they always share one version
and are published together. Releases go to PyPI automatically when a version tag
is pushed, authenticated with a PyPI API token.

## One-time setup

1. Create an **account-scoped** API token at
   <https://pypi.org/manage/account/token/>. (Account scope is required because
   the projects do not exist on PyPI yet; you can rotate to project-scoped tokens,
   or switch to Trusted Publishing, after the first release.)

2. Store it as a secret named `PYPI_API_TOKEN` in the `pypi` GitHub Environment:

   ```bash
   gh secret set PYPI_API_TOKEN --env pypi --repo byunjuneseok/fast-feature
   ```

   (The `pypi` environment already exists; optionally add protection rules such as
   required reviewers to gate publishing.)

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
  to the publish step and use a TestPyPI token.
