# Release Guide

This project includes `.github/workflows/release.yml` so a GitHub Release can be produced automatically after the repository exists.

## Release

1. Open **Actions**.
2. Select **Build Heavy Scanner Release**.
3. Select **Run workflow**.
4. Enter a tag such as `v1.0.0`.
5. The workflow generates the 15K+ line fixture, installs requirements, runs pytest, packages the project and creates a GitHub Release with the tarball attached.

The workflow uses `contents: write` only for the release operation.
