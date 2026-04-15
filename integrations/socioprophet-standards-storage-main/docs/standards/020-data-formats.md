# Data Formats Standard: Avro, Arrow, Parquet, JSON-LD, Schema Packaging

## Avro (event contracts)
- Avro is the canonical schema for event topics and durable event records.
- Avro schemas MUST be stored in-repo and registered with a schema registry (or equivalent compatibility gate).

## Arrow (in-memory interchange)
- Arrow is the canonical in-memory representation for feature matrices, embedding batches, and analytic payloads.
- Services MAY use Arrow IPC or Arrow Flight for high-throughput transfer.

## Parquet (durable columnar)
- Parquet is the canonical durable columnar format in object storage.
- Parquet datasets MUST include a manifest with: schema version, partitioning, content hashes.

## JSON-LD (semantic/provenance overlay)
- JSON-LD is used to publish a semantics/provenance layer (PROV-O, TIME, etc.).
- JSON-LD contexts MUST be versioned and mapped deterministically from Avro IDs/fields.

## Schema/Workflow packaging
- Schema and pipeline artifact sets MUST be packaged with validators (SchemaSalad or equivalent) so CI can prove consistency.

