# C268 historical hinge endpoint admission

C268 implements the fourth C260 interface, `read_bound_endpoint(repo, endpoint)`, for the original `before` and `after` source/GLB byte tuples. The current checkpoint contains implementation and initial self-check evidence; independent controls, review, integration and saved final delivery remain pending.

The reader admits exact sizes/hashes through bounded descriptor-relative reads, refuses symlink files/ancestors, escapes and nonregular files, and supplies captured bytes to the pinned C267 finite comparator. Its five-module dependency closure is captured anew before each call; the scoped acquisition hooks avoid later path reopening. See [implementation](IMPLEMENTATION.md), [input bindings](INPUTS.json), [requirements](../../workflow/tasks/C268/REQUIREMENTS.md) and [plan](../../workflow/tasks/C268/PLAN.md).

Historical admission means only that the original recorded bytes were read and their finite hinge declarations compared. Accepted source revisions, edit atomicity, clean rebuilds, site poses/world behavior, full source/glTF/C255 validity, native/model trial success and comparative benefit remain unqualified. Existing raw changed-input interfaces are unchanged.
