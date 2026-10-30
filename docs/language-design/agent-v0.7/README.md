# Agent/0.7 execution-budget contract

Read [ADOPTION.md](ADOPTION.md) for the separately versioned C074 decision, authority model, lifecycle and current scope. It extends explicit source `0.7` to a durable Agent service while preserving all earlier protocols and defaults.

- [request.schema.json](request.schema.json) defines the exact twelve operation shapes, optional execution reductions and source-file patch scope.
- [response.schema.json](response.schema.json) defines the versioned envelope and execution receipt.
- [diagnostic.schema.json](diagnostic.schema.json) preserves the inherited revision-bound diagnostic shape with the C074 resource-reason contract.
- [conformance-c074.json](conformance-c074.json) maps the five inherited deferred cases to new lifecycle tests. The original preparation plan is unchanged.

Schema validity checks structure. It cannot authorize a host ceiling, verify a source hash, execute an operation, establish a valid numerical prefix or prove a destination artifact. Actual runtime, integration and release evidence must identify their source revision and measured results separately.
