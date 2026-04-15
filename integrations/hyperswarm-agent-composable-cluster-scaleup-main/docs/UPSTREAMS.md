# Upstreams (Pinned)

We pin upstream repos + refs in `tools/upstreams.env` and fetch them into `third_party/`.

Pinned choices (evidence):
- Kubespray: GitHub Releases include v2.29.1 (Dec 2025).
- Krew: GitHub shows v0.4.5 (Mar 2025).
- Fybrik / Mesh-for-Data lineage: GitHub Releases include v1.3.3 (May 2023).
- Heroku buildpack apt: GitHub indicates no Releases; treated as legacy reference only.

Linkages:
- This wrapper is meant to be referenced by `SocioProphet/prophet-platform` in infra/docs.
- Cross-repo validation and inventory should be enforced by `SocioProphet/sociosphere`.
