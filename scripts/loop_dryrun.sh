#!/usr/bin/env bash
# loop_dryrun — exercise the WHOLE compounding loop once, end to end:
#   submit verified SFT → Atlas Ray LoRA train → promote-never-demote gate → hot-load adapter → serve.
#
# This is the ONE paid run. Everything upstream is $0-validated (unit tests + tiny-gpt2 + live
# endpoints), so the first time a real GPU spins is here. Steps 1–3 hit only Atlas (atlasd); steps
# 4–5 touch the serving cluster. Pass --atlas-only to stop after the gate (no cluster needed — used
# for the local $0 validation).
#
# Env:
#   ATLAS_HTTP          atlasd base url (default http://127.0.0.1:8000)
#   SFT_URI             verified SFT dataset the trainer reads (gs://… or a path)   [required]
#   BASE_MODEL          default Qwen/Qwen2.5-Coder-7B-Instruct
#   ATLAS_OPT_IN_TOKEN  opt-in token if atlasd requires one
#   GPU                 GPUs to request (default 1; set 0 for a CPU/local run)
#   ADAPTER_GCS         where the trainer uploaded the adapter (default gs://noetica-brains/adapters/lora-verified)
#   SERVE_NS            serving namespace (default serving)
set -uo pipefail

ATLAS_HTTP="${ATLAS_HTTP:-http://127.0.0.1:8000}"
SFT_URI="${SFT_URI:?set SFT_URI to the verified SFT dataset (gs://… or a trainer-readable path)}"
BASE_MODEL="${BASE_MODEL:-Qwen/Qwen2.5-Coder-7B-Instruct}"
GPU="${GPU:-1}"
ADAPTER_GCS="${ADAPTER_GCS:-gs://noetica-brains/adapters/lora-verified}"
SERVE_NS="${SERVE_NS:-serving}"
ATLAS_ONLY=0; [ "${1:-}" = "--atlas-only" ] && ATLAS_ONLY=1

HDR=(-H 'content-type: application/json')
[ -n "${ATLAS_OPT_IN_TOKEN:-}" ] && HDR+=(-H "X-Opt-In-Token: ${ATLAS_OPT_IN_TOKEN}")
say() { printf '\n\033[1m== %s ==\033[0m\n' "$*"; }
jget() { python3 -c "import sys,json;d=json.load(sys.stdin);print($1)" 2>/dev/null; }

# ── 1. submit ───────────────────────────────────────────────────────────────────────────────────
say "1/5 submit causal_lm_lora job → ${ATLAS_HTTP}/v1/tune"
REQ=$(printf '{"tenant":"noetica","task":"generation","entrypoint":"causal_lm_lora","metric":"pass_at_1","mode":"max","base_model":"%s","train":{"uri":"%s"},"peft":{"r":16,"alpha":32},"resources":{"CPU":4,"GPU":%s,"MEM":24},"use_ray":true}' "$BASE_MODEL" "$SFT_URI" "$GPU")
JOB=$(curl -sf "${HDR[@]}" -X POST "${ATLAS_HTTP}/v1/tune" -d "$REQ" | jget 'd["id"]')
[ -z "$JOB" ] && { echo "  submit failed"; exit 1; }
echo "  job: $JOB"

# ── 2. train (poll) ───────────────────────────────────────────────────────────────────────────────
say "2/5 train (Ray LoRA) — polling status"
for i in $(seq 1 240); do
  ST=$(curl -sf "${HDR[@]}" "${ATLAS_HTTP}/v1/jobs/${JOB}/status" | jget 'd.get("state","")')
  echo "  [$i] ${ST:-?}"
  case "$ST" in SUCCEEDED) break;; FAILED) echo "  ✗ train failed"; exit 1;; esac
  sleep 15
done

# ── 3. promote (held-out eval gate: pass@1 base vs base+adapter) ──────────────────────────────────
say "3/5 promote — held-out eval gate (promote-never-demote)"
REP=$(curl -sf "${HDR[@]}" -X POST "${ATLAS_HTTP}/v1/jobs/${JOB}/promote")
echo "$REP" | python3 -m json.tool 2>/dev/null || echo "$REP"
OK=$(echo "$REP" | jget 'str(d.get("ok", (d.get("gates",{}).get("eval_delta",{}) or {}).get("ok", False))).lower()')
if [ "$OK" != "true" ]; then
  echo "  ⛔ GATE BLOCKED — the adapter did not beat the base on held-out pass@1. Not serving."
  echo "     (promote-never-demote did its job; the served model is unchanged.)"
  exit 0
fi
echo "  ✅ gate PASSED — adapter beats/matches base."
[ "$ATLAS_ONLY" = "1" ] && { echo "  --atlas-only: stopping before serving (no cluster)."; exit 0; }

# ── 4. hot-load the promoted adapter into the running mesh (no redeploy) ───────────────────────────
say "4/5 hot-load promoted adapter into mesh-vllm"
SERVED_ID="noetica-lora-${JOB}"
gsutil -m cp -r "$ADAPTER_GCS" ./_adapter
POD=$(kubectl -n "$SERVE_NS" get pod -l app=mesh-vllm -o name | head -1)
kubectl -n "$SERVE_NS" cp ./_adapter "${POD#pod/}:/tmp/${SERVED_ID}"
kubectl -n "$SERVE_NS" exec "$POD" -- curl -sf -X POST localhost:8000/v1/load_lora_adapter \
  -d "{\"lora_name\":\"${SERVED_ID}\",\"lora_path\":\"/tmp/${SERVED_ID}\"}"

# ── 5. verify the served adapter answers ──────────────────────────────────────────────────────────
say "5/5 verify served adapter"
kubectl -n "$SERVE_NS" exec "$POD" -- curl -sf -X POST localhost:8000/v1/chat/completions \
  -H 'content-type: application/json' \
  -d "{\"model\":\"${SERVED_ID}\",\"max_tokens\":80,\"messages\":[{\"role\":\"user\",\"content\":\"Write a Python is_prime(n) function.\"}]}" \
  | jget 'd["choices"][0]["message"]["content"][:240]'

echo ""
echo "🔁 LOOP CLOSED: trained → gated → promoted → served as ${SERVED_ID}."
echo "   Point noetica MESH_MODEL / NOETICA_SOVEREIGN_MODEL at '${SERVED_ID}' to use the sharper model."
