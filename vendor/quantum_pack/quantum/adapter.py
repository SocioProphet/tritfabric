# quantum/adapter.py
# Small adapter that uses Qiskit Estimator/Sampler locally (Aer) or via IBM Runtime if present.
# Provides: QuantumChargeProjector (expectation values), QAOAScheduler (toy MaxCut on heavy-hex-like graphs).

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict
import math, os

try:
    from qiskit import QuantumCircuit
    from qiskit.quantum_info import SparsePauliOp
    try:
        # Local primitives (Qiskit 1.x)
        from qiskit.primitives import Estimator
    except Exception:
        Estimator = None
    try:
        # Aer-specific primitives if installed
        from qiskit_aer.primitives import Estimator as AerEstimator
    except Exception:
        AerEstimator = None
    try:
        # IBM Runtime (optional)
        from qiskit_ibm_runtime import QiskitRuntimeService, Estimator as RuntimeEstimator, Options
    except Exception:
        QiskitRuntimeService = None
        RuntimeEstimator = None
        Options = None
except Exception as e:
    QuantumCircuit = None
    SparsePauliOp = None
    Estimator = AerEstimator = RuntimeEstimator = None

@dataclass
class BackendConfig:
    provider: str = "aer"   # "aer" | "ibm"
    backend: Optional[str] = None  # "heron", "osprey", ... (advisory)
    shots: int = 2000
    mitigation: Tuple[str,...] = ("m3","zne")

class QuantumChargeProjector:
    def __init__(self, cfg: BackendConfig):
        self.cfg = cfg
        self.estimator = self._make_estimator()

    def _make_estimator(self):
        # Prefer IBM runtime if provider == "ibm" and runtime lib available
        if self.cfg.provider == "ibm" and RuntimeEstimator is not None and QiskitRuntimeService is not None:
            svc = QiskitRuntimeService(channel="ibm_quantum")  # assumes env auth
            opts = Options()
            # mitigation flags are advisory; actual knob names may differ by version
            opts.execution.shots = self.cfg.shots
            return RuntimeEstimator(session=svc, options=opts)
        # Else prefer Aer Estimator if present
        if AerEstimator is not None:
            return AerEstimator(approximation=True, shots=self.cfg.shots)
        # Fallback to local Estimator (may be statevector, noiseless)
        if Estimator is not None:
            return Estimator()
        raise RuntimeError("No Qiskit Estimator available. Install qiskit or qiskit-aer or qiskit-ibm-runtime.")

    def estimate(self, circuit: "QuantumCircuit", pauli: "SparsePauliOp") -> Tuple[float,float]:
        job = self.estimator.run(circuits=[circuit], observables=[pauli])
        res = job.result()
        mean = float(res.values[0])
        var = float(res.metadata[0].get("variance", 0.0))
        return mean, var

# --------- QAOA Scheduler (toy) ---------
def heavy_hex_subgraph(n: int) -> List[Tuple[int,int]]:
    """Generate a sparse degree-3-ish 'heavy-hex-like' subgraph with n nodes (not exact IBM map)."""
    edges = set()
    # base ring
    for i in range(n):
        edges.add((i, (i+1)%n))
    # add chords every 6 steps
    for i in range(0, n, 6):
        j = (i+3) % n
        edges.add((i, j))
    # add vertical-ish links
    for i in range(0, n, 2):
        edges.add((i, (i+2)%n))
    return sorted({tuple(sorted(e)) for e in edges})

def maxcut_cost_op(n: int, edges: List[Tuple[int,int]]) -> "SparsePauliOp":
    # H = sum_{(i,j) in E} (I - Z_i Z_j)/2
    terms = []
    coeffs = []
    for (i,j) in edges:
        z = ["I"]*n
        z[i] = "Z"; z[j] = "Z"
        terms.append("".join(reversed(z)))  # Qiskit uses little-endian
        coeffs.append(-0.5)  # -Z_i Z_j / 2
    # + |E|/2 * I
    from qiskit.quantum_info import SparsePauliOp
    H = SparsePauliOp.from_list([(t, c) for t,c in zip(terms, coeffs)])
    return H, len(edges)/2.0

def qaoa_ansatz(n: int, edges: List[Tuple[int,int]], p_layers: int, gammas: List[float], betas: List[float]) -> "QuantumCircuit":
    from qiskit import QuantumCircuit
    qc = QuantumCircuit(n)
    # initial state |+>^n
    for q in range(n): qc.h(q)
    # cost + mixer
    for l in range(p_layers):
        gamma = gammas[l]; beta = betas[l]
        # cost: for each edge, implement exp(-i * gamma * Z_i Z_j)
        for (i,j) in edges:
            qc.cx(i,j); qc.rz(-2*gamma, j); qc.cx(i,j)
        # mixer: Rx(2*beta) on all qubits
        for q in range(n): qc.rx(2*beta, q)
    return qc

class QAOAScheduler:
    def __init__(self, cfg: BackendConfig):
        self.cfg = cfg
        self.projector = QuantumChargeProjector(cfg)

    def run_grid_search(self, n=16, p_layers=2, gamma_grid=(-1.0,0.0,1.0), beta_grid=(0.3,0.7)):
        edges = heavy_hex_subgraph(n)
        H, shift = maxcut_cost_op(n, edges)
        best = None
        for g in gamma_grid:
            for b in beta_grid:
                gammas = [g]*p_layers; betas = [b]*p_layers
                qc = qaoa_ansatz(n, edges, p_layers, gammas, betas)
                mean, _ = self.projector.estimate(qc, H)
                energy = mean + shift  # add constant shift
                score = -energy        # MaxCut: lower energy = better cut
                cand = {"gammas":gammas, "betas":betas, "energy":energy, "score":score}
                if best is None or score > best["score"]:
                    best = cand
        best["n"]=n; best["edges"]=len(edges)
        return best
