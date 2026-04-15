# Org placement and repo split plan

This repo intentionally contains *both* runtime and training-side scaffolds, because the original TritFabricAI work
crossed the boundary between:
- **SourceOS** (operational runtime, user machines, opt-in automation) and
- **SocioProphet** (model customization/training, evaluation, standards/governance).

For long-term hygiene, we recommend splitting **by trust boundary and operator persona**, not by language.

---

## Recommended placement (strong default)

### Socios-linux org
Owns anything that:
- runs on end-user systems (desktop/laptop/edge nodes),
- touches OS automation, device access, local secrets, or daemonization,
- must default to **disabled** until explicit opt-in.

Place here:
- **Atlas daemon packaging + opt-in wiring**
  - systemd units, launch scripts, desktop prompts, local socket permissions
  - SourceOS hooks, MCP servers, A2A bootstrap integration
- **Runtime adapters** needed by SourceOS
  - local inference adapters, “bring your own model” wiring
  - local-only storage spooling, offline-first carriers

Repo suggestions:
- `Socios-linux/atlas-os-service` (daemon + runtime)
- `Socios-linux/sourceos-tritfabric-integration` (thin glue, if we keep Atlas elsewhere)

### SocioProphet org
Owns anything that:
- defines canonical specs/contracts/standards,
- runs in platform environments (k8s, CI, training clusters),
- concerns model training, evaluation, governance, or storage/graph standards.

Place here:
- **Protocol + canonical contracts**
  - `tritrpc` remains canonical
  - shared `.proto` API surfaces
- **Training and evaluation platform**
  - Slate training stack, experiment configs, eval harness
- **Standards + ontologies**
  - storage standards, ontogenesis, SHACL shapes, JSON-LD contexts
- **Platform GitOps**
  - ArgoCD appsets for Prophet platform components

Repo suggestions:
- `SocioProphet/tritfabric-spec` (proto + JSON-LD + SHACL + invariants + conformance tests)
- `SocioProphet/prophet-platform` (already exists)
- `SocioProphet/tritrpc` (already exists)
- `SocioProphet/socioprophet-standards-storage` (already exists)
- `SocioProphet/ontogenesis` (already exists)

---

## “Both” category (deliberate duplication, but controlled)

Some assets belong in both orgs **as immutable copies**, because SourceOS must run offline,
while Prophet must operate at scale.

The safest pattern:
- canonical source in **SocioProphet**,
- pinned, vendored copies in **Socios-linux** with explicit version pinning and attestation.

Examples:
- protobuf API surface + generated stubs
- SHACL shapes + JSON-LD contexts
- Gatekeeper policy templates (if SourceOS includes k8s automation)
- minimal “conformance test vectors” for promotion gates

Mechanism:
- publish versioned release artifacts (zip, OCI artifact, or git tag)
- SourceOS consumes by digest (SLSA provenance strongly recommended)

---

## Why TritFabric/Atlas should not live only in one org

If we put everything in Socios-linux:
- we risk dragging training/governance into OS land (bad boundary hygiene).

If we put everything in SocioProphet:
- we risk runtime/opt-in details leaking into platform repos and accidentally enabling features by default.

So we keep:
- **specs and platform** in SocioProphet,
- **opt-in runtime distribution** in Socios-linux.

This repo remains a “consolidated working tree” until we complete the split.
