# TritFabric Quantum Pack

This pack adds a **quantum lane** to your publishing + proof system.

## Contents
- `configs/tritfabric_quantum.yaml` — drop-in config for the lane (provider, backend policy, tasks).
- `quantum/adapter.py` — `QuantumChargeProjector` (Pauli expectations) and `QAOAScheduler` (toy MaxCut on heavy-hex-like subgraphs).
- `notebooks/demo_quantum_lane.ipynb` — runs SU(2) charge + 64-node QAOA and writes `out/` artifacts.
- `publish/publish_proof.sh` — renders Markdown → PDF and signs it with OpenSSL.
- `cli/demo_publish.py` — executes the notebook and publishes the signed PDF proof.

## Quickstart
```bash
# (1) Run the notebook and publish the proof
python cli/demo_publish.py

# (2) Or run manually
# Execute:
jupyter nbconvert --to notebook --execute --output out/demo_quantum_lane.executed.ipynb notebooks/demo_quantum_lane.ipynb
# Render + sign:
./publish/publish_proof.sh signing_key.pem   # create a key via: openssl genrsa -out signing_key.pem 2048
```

## Provider notes
- **Default** uses local Qiskit or `qiskit-aer` primitives.
- To use IBM hardware, export:
```bash
export TF_QUANTUM_PROVIDER=ibm
export QISKIT_IBM_TOKEN=...   # ensure qiskit-ibm-runtime is installed and configured
```
The notebook will attempt to use IBM Runtime Estimator if available; otherwise falls back to Aer.

## Dependencies
- `qiskit` (and optionally `qiskit-aer`, `qiskit-ibm-runtime`)
- `jupyter`, `nbconvert`, `pandoc`, `openssl`

## Provenance
- `out/provenance.json` captures backend, parameters, and results.
- `out/report.md` → `out/report.pdf`, signed with `out/report.sig` (+ Base64 form).

## Security
- Keys never leave your machine. PDF signing uses OpenSSL with RSA-2048 SHA-256.
