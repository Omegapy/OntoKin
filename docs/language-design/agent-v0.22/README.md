# Finite torque Agent/0.22 contract

This proposed explicit binding is defined by [the source contract](../torque-v0.1/SPECIFICATION.md), [Agent lifecycle](../torque-v0.1/AGENT.md), [closed torque state](../torque-v0.1/torques.schema.json) and [recording contract](../torque-v0.1/RECORDING.md). A separate C090 adoption binds reviewed bytes before runtime implementation.

The [request](request.schema.json), [response](response.schema.json) and [diagnostic](diagnostic.schema.json) schemas derive from untouched Agent/0.21. [SCHEMA-DERIVATION.json](SCHEMA-DERIVATION.json) identifies every baseline hash, binding scalar change and additive projection path. Existing operations and bundle/files 0.2 stay unchanged. Closed `torques` records are mandatory on available .22 object states; source occurrence histories and the new torque discovery interface are separately defined. Unavailable source/definition states retain their actual inherited shapes.

The new store is `torque-program-agent.sqlite3`, schema `ontokin.torque-program-agent-store/0.1`. Earlier protocols and defaults remain unchanged. No torque runtime support or complete experimental release is claimed by these files.
