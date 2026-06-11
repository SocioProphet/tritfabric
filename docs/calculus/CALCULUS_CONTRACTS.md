# Calculus Contracts

**Status:** planned. Fields defined in model card spec; SHACL enforcement not yet in CI.
**Rule:** Every model artifact must carry `math_type` and `calc_ops`. A model card without these fields fails the `calculus_checked` promotion gate — hard stop.

---

## 1. Why calculus contracts exist

Without declared mathematical roots, a model card is a marketing document. It can claim "transformer-based" or "manifold-aware" without specifying what mathematical operations are actually performed, over what space, with what guarantees.

Calculus contracts give every model artifact machine-auditable mathematical roots: a declared type system for the math, a declared set of operations, and a SHACL validation gate that enforces both at promotion time.

This is not academic overhead. It is what separates "I claim this model uses Riemannian geometry" from "this model's card declares `math_type: riemannian_manifold` and `calc_ops: [exponential_map, parallel_transport, geodesic_distance]`, and those declarations passed SHACL validation against the calculus type registry."

---

## 2. Required model card fields

Every model card must declare:

### `math_type`

The mathematical structure the model's core computation operates over.

Must reference a type in the Calculus Type Registry (Section 4). Free-form strings are rejected.

Examples:
```
euclidean_vector_space
riemannian_manifold
ternary_logic_space
hilbert_space
directed_graph
```

### `calc_ops`

The specific mathematical operations the model uses. An array. Each entry must be in the Operations Registry (Section 5).

Examples:
```yaml
calc_ops:
  - gradient_descent
  - attention_softmax
  - layer_normalization
```

```yaml
calc_ops:
  - ternary_matmul
  - ternary_accumulation
  - sign_activation
```

---

## 3. SHACL enforcement

A SHACL shape validates every model card at promotion time:

```turtle
# calculus-contract.shacl.ttl (planned — not yet in CI)
ex:ModelCardShape
  a sh:NodeShape ;
  sh:targetClass ex:ModelCard ;
  sh:property [
    sh:path ex:math_type ;
    sh:minCount 1 ;
    sh:in ex:MathTypeRegistry ;
    sh:message "math_type must be present and in the type registry"
  ] ;
  sh:property [
    sh:path ex:calc_ops ;
    sh:minCount 1 ;
    sh:in ex:CalcOpsRegistry ;
    sh:message "calc_ops must be non-empty and all entries must be in the operations registry"
  ] .
```

The SHACL gate runs in CI before any model card is accepted as a promotion artifact. Failure is a hard stop — not a warning.

---

## 4. Calculus Type Registry (initial)

| Type | Description |
|---|---|
| `euclidean_vector_space` | Standard ℝⁿ with L2 norm |
| `riemannian_manifold` | Curved differentiable manifold with metric tensor |
| `hilbert_space` | Complete inner-product space (functional analysis) |
| `ternary_logic_space` | {-1, 0, +1} valued computation |
| `directed_graph` | Graph with directed edges and node features |
| `hypergraph` | Graph with hyperedges connecting arbitrary node sets |
| `simplex` | Probability simplex (softmax output lives here) |
| `lie_group` | Differentiable group with Lie algebra |
| `symplectic_manifold` | Phase space with preserved symplectic form |

To add a type: open a PR updating this registry and the SHACL shape. Do not use undeclared types in model cards.

---

## 5. Operations Registry (initial)

| Operation | Type context | Description |
|---|---|---|
| `gradient_descent` | euclidean_vector_space | Standard SGD/Adam step |
| `attention_softmax` | euclidean_vector_space | Scaled dot-product attention |
| `layer_normalization` | euclidean_vector_space | LayerNorm |
| `ternary_matmul` | ternary_logic_space | Matmul over {-1, 0, +1} |
| `ternary_accumulation` | ternary_logic_space | Popcount-based accumulation |
| `sign_activation` | ternary_logic_space | Sign/step activation |
| `exponential_map` | riemannian_manifold | Geodesic projection from tangent space |
| `parallel_transport` | riemannian_manifold | Move vector along geodesic |
| `geodesic_distance` | riemannian_manifold | Distance along manifold |
| `lie_bracket` | lie_group | Commutator of Lie algebra elements |
| `graph_message_passing` | directed_graph | Aggregate neighbor features |
| `hyperedge_contraction` | hypergraph | Reduce hyperedge to node |

To add an operation: open a PR updating this registry. Include the type context and a one-line description.

---

## 6. No-vapor rule

A model card may not declare a `math_type` or `calc_op` that is not in the registries above. This prevents:
- Vague claims ("advanced geometric AI") that cannot be validated.
- Aspirational declarations of math that is not actually implemented.
- Registry drift where model cards reference types that no other artifact uses.

If a model genuinely uses a new mathematical structure, add it to the registry first, then declare it in the model card. The PR for the registry addition is itself the evidence that the type is real.

---

## 7. Calculus contract in the Cainpath CairnLine

The `calculus_checked` CairnStep in an Atlas job's CairnLine cites:
- The model card ref (content hash).
- The SHACL validation result (pass/fail).
- The `math_type` and `calc_ops` values that were validated.

This makes the calculus contract part of the replayable promotion evidence, not a separate out-of-band check.
