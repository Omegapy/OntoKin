# C210 direction and preservation review

## Result

The reviewed drafts adopt the user's revised semantic-authoring direction and
keep the executable proof explicitly in progress. No blocking scope violation,
frozen-protocol modification, silent completion claim, or roadmap/comparison
omission was found. Two small documentation clarifications are recommended
before publication.

This is a read-only scope review, not an implementation approval. The semantic
contract, proof result and Unreal boundary were still forthcoming and their
temporary missing paths were not treated as defects.

## Actionable points

1. **Describe the prior interoperability policy precisely.**
   GOAL.md paragraph after the roadmap says the former policy deferred
   “every new interoperability experiment”; DECISION.md repeats “every new
   destination experiment.” At starting main, GOAL.md deferred a general
   importer, capture pipeline or new production backend until comparative
   evidence justified the expense. It did not literally ban every small
   interoperability experiment. Replace the broad historical characterization
   with the actual old restriction, then state that C210 explicitly permits the
   three bounded feasibility stages while broader investment still requires
   measured benefit. The intended new priority is already clear.

2. **Make the remaining old domain dispositions explicit.**
   The decision table classifies the major language, geometry, physics,
   creature/vehicle/fluid, gameplay and study directions. STATUS additionally
   lists terrain/buildings, appearance/textures, animation transitions/live
   engines, scale and performance as older uncompleted ambitions, but their
   individual disposition is less explicit. One short table row can state
   that existing supported geometry/material/animation behavior remains
   current, while unimplemented extensions in these areas are deferred until
   a demonstrated authoring or interoperability need. This avoids suggesting
   that every unresolved obligation disappeared with the universal
   world-building completion criterion.

Neither point requires changing frozen or historical records.

## Confirmed alignment

- README, GOAL, STATUS, AGENTS and active navigation consistently prioritize
  source-authoritative semantic construction, inspection, validation, repair
  and checked transport.
- They keep the existing normalized representation and explicitly avoid new
  syntax, a new Agent protocol, a parallel representation and simultaneous
  backends.
- C209 job/0.2 retained-result compatibility and C201 preparation/admission are
  explicitly deferred; C199/C200 schedules remain closed.
- Unreal/Verse are intended targets. No implemented destination, universal
  physical behavior or measured authoring benefit is claimed.
- The four roadmap stages occur in the requested order. Only stage one belongs
  to this milestone.
- The comparison retains matched direct tools, unseen variants, comparable
  model/tool/resources, predefined correctness/preservation/recovery/
  reproducibility/time-token/reuse measures, and scope reassessment if direct
  tools perform comparably. C180 remains linked for the detailed study design.
- Ordinary budgets, adopted semantics, failed/unrun regressions, C208's original
  timing failure and separate pass, validation rules and serialized integration
  rules remain intact.
- The exact previous GOAL is linked at immutable starting commit
  `94dee707c148b7a545e43d4de0d601642c5fa3e8` from both current GOAL and DECISION.
  The referenced Git object exists locally and contains the complete prior
  direction. Older PRD/CAP records remain linked.

## Frozen-file verification

Direct byte comparison against starting main found all four files unchanged:

- docs/engineering/static-tray-admission-c201/README.md
- docs/engineering/static-tray-admission-c201/ADMISSION.md
- docs/engineering/static-tray-admission-c201/ADMISSION.json
- docs/engineering/static-tray-admission-c201/IMPLEMENTATION-NEXT.md

`INPUTS-AND-FROZEN.json` records their baseline/current SHA-256 hashes, all six
reviewed file hashes, the prior GOAL hash and immutable-link checks.

## Closure reminder

After proof validation, replace the current in-progress status and current
action with the actual result and one exact next action. Keep remaining gates
visible if the proof is partial. Run the required documentation preservation/
link check once the forthcoming files exist. This review does not claim that
check or any implementation/visual gate passed.

