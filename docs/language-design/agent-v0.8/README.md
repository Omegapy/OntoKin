# Agent/0.8 polygon extrusion contract

The [C075 adoption](../polygon-extrusion-v0.1/ADOPTION.md) explicitly selects source 0.8, polygon-extrusion-0.1, Agent/0.8 and recorded GLB/0.8. Earlier bindings and defaults remain unchanged.

- [request.schema.json](request.schema.json) defines the twelve operation shapes, execution caps and exact source-file edits
- [response.schema.json](response.schema.json) defines the envelope, execution receipt, polygon summaries and bounded mesh pages
- [diagnostic.schema.json](diagnostic.schema.json) retains the existing source-bound diagnostic shape

`ExtrusionAgentService` uses `extrusion-program-agent.sqlite3` with store schema `ontokin.extrusion-program-agent-store/0.1`. It preserves C074 request authorization, cancellation, retries and atomic publication. Its mesh-page profile identifies polygon-extrusion-0.1. Inherited loft summaries retain their original surface schema; polygon summaries use ontokin.polygon-extrusion-summary/0.1.

Schema validity describes structure. Executed source workflows, geometry, delivery, integration and release evidence remain separately identified.
