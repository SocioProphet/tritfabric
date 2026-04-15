# Operator Runbook — TritFabric (Atlas OS Service)

This runbook assumes:
- ArgoCD for GitOps sync
- Argo Rollouts for canary
- (Optional) Argo Workflows/Events for CI-as-pipelines
- Gatekeeper for baseline policy hardening
- Vault + ExternalSecrets for secret distribution

---

## 0) Install prerequisites (cluster)

ArgoCD:
```bash
kubectl create ns argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

Argo Rollouts:
```bash
kubectl create ns argo-rollouts
kubectl apply -n argo-rollouts -f https://raw.githubusercontent.com/argoproj/argo-rollouts/stable/manifests/install.yaml
```

(Optional) Workflows/Events:
```bash
kubectl create ns argo
kubectl apply -n argo -f https://raw.githubusercontent.com/argoproj/argo-workflows/stable/manifests/quick-start-minimal.yaml
kubectl apply -n argo -f https://raw.githubusercontent.com/argoproj/argo-events/stable/manifests/install.yaml
```

---

## 1) Build and publish images

This repo ships Dockerfiles for:
- `tritfabric-server` (atlasd)
- `tritfabric-sse` (SSE gateway)
- `tritfabric-tools` (promotion gates job)

Example:
```bash
export ORG=your-org
docker build -t ghcr.io/$ORG/tritfabric-server:latest -f Dockerfile.server .
docker build -t ghcr.io/$ORG/tritfabric-sse:latest -f Dockerfile.sse .
docker build -t ghcr.io/$ORG/tritfabric-tools:latest -f Dockerfile.tools .
docker push ghcr.io/$ORG/tritfabric-*:latest
```

CI publishing:
- `.github/workflows/publish.yml` builds/pushes on `main`.

---

## 2) GitOps bootstrap (ArgoCD AppSet)

1) Commit this repo to Git.
2) Edit:
- `deploy/argo/argocd/applicationset.yaml` → set your repo URL.
3) Apply:
```bash
kubectl apply -n argocd -f deploy/argo/argocd/projects.yaml
kubectl apply -n argocd -f deploy/argo/argocd/applicationset.yaml
```

Expected:
- ArgoCD syncs dev/stage/prod namespaces.

---

## 3) Secrets (Vault + ExternalSecrets)

This repo provides templates under:
- `deploy/argo/apps/tritfabric-system/secrets/`

Put keys in Vault:
- `tritfabric/aead` (base64 key or token)

Apply SecretStore + ExternalSecret:
```bash
kubectl apply -f deploy/argo/apps/tritfabric-system/secrets/
```

Restart gateways to pick up new secrets.

---

## 4) Gatekeeper (baseline hardening)

Install:
```bash
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/stable/deploy/gatekeeper.yaml
```

Apply templates + constraints:
```bash
kubectl apply -f deploy/argo/gatekeeper/templates/
kubectl apply -f deploy/argo/gatekeeper/constraints/
```

Gradual rollout:
- start with audit/warn,
- enforce in prod only once violations are resolved.

Required labels:
- `app.kubernetes.io/part-of: tritfabric`
- `plane: serve|ai|msg|...`

---

## 5) Observability (Prometheus + Grafana)

- Atlas metrics endpoint: `:9108/metrics`
- Import dashboard from: `grafana/atlas-observability-dashboard.json`

---

## 6) Promotion and rollout

Promotion gates live in the **tools** image.
Typical pattern:
- promotion is **fail-closed**
- Rollouts analysis runs:
  1) SLO check (Prometheus)
  2) gates job (tools) — SHACL + ONNX cosine + eval delta

---

## 7) Common issues

- Image not updating:
  - Image Updater not running or app annotations missing.
- Rollout stuck:
  - analysis metric or gates job failing; check Rollouts events.
- SHACL fails:
  - inspect `artifacts/<job_id>/shacl_report.txt` (if enabled).
- Signature verification fails:
  - missing AEAD key or wrong format; check gateway logs.
