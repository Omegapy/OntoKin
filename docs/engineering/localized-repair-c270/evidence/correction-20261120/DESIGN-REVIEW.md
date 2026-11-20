# C270 classification correction: independent design review

Reviewer: `/root/github_reconcile`.
Inspected starting revision: `55c585acdaa750961ac37a5c46c9160bed149f97`.
Review status: design boundary accepted; exact-candidate approval pending.

## Scope and independence

This review concerns only the existing C270 R02 defect: the independently frozen, source-valid declared `SiteRef` parameter is currently classified as `MALFORMED`, while the unchanged oracle requires `UNSUPPORTED_SOURCE_FORM`. The reviewer derived expectations from the adopted specifications and frozen C260/C270 documents before reading `source_hinges.py`. No observer, evaluator, exporter, native application, or model trial was executed during this design review. The reviewer made no repository or GitHub mutation.

The Director owns the declared correction phase, lease, commits, integration, tests and saved handoff. The shared checkout remained at the stated HEAD during this inspection, with Director-owned workflow/phase files being prepared. Those uncommitted files are not an approved candidate.

## Proposed classification boundary

An endpoint whose actual terminal member is an explicitly visible `param`, with exactly the single identifier token `SiteRef` as its declared type, may be refused as `UNSUPPORTED_SOURCE_FORM` after the existing name, key, structural and access checks. The declaration must exist in the resolved lexical class. A private member is accessible within its own declaring class; a terminal member reached through another class must be public in this finite profile.

This predicate identifies an excluded source form. It does not prove that the whole source is valid or that the parameter's initializer is well typed, acyclic, resolvable, or equal to any site. The observer must not evaluate, resolve, follow or substitute the initializer. The frozen case's validity is separately established by the preserved `SOURCE-VALIDITY.md` argument and exact input bytes. No supported successful observation form is added.

This treatment follows C260 CONTRACT sections 1, 3.3 and 6: the finite observer is smaller than the language; parameter/computed `SiteRef` forms are excluded; unsupported forms must be distinguished from malformed input. The core specification sections 5.1, 6.1–6.3, 7.2–7.3 and 10.2 supply the type/member/access rules. The construction specification sections 1 and 3.1 retain those rules, and its `property_decl` grammar requires authored visibility.

## Mandatory distinctions for candidate review

The candidate must preserve these terminal-member outcomes:

| Case | Required treatment |
| --- | --- |
| Unchanged frozen own-class private `SiteRef` parameter | `UNSUPPORTED_SOURCE_FORM`; no alias evaluation or successful/partial set |
| Own-class public `SiteRef` parameter | Same unsupported refusal |
| Public `SiteRef` terminal on the existing directly owned private part | Accessible unsupported refusal; private own-part traversal remains legal |
| Private `SiteRef` terminal on another declaring class | `MALFORMED` before the new unsupported predicate |
| Missing terminal name | `MALFORMED` |
| Terminal parameter declared `FrameRef`, `Length`, or another non-`SiteRef` type | `MALFORMED` |
| Existing terminal of another member kind | Existing refusal; it must not be classified by name or initializer alone |
| `SiteRef<Real>`, a qualified type, quoted `"SiteRef"`, or extra type tokens | `MALFORMED`; exact nominal type recognition only |
| Missing authored parameter visibility | `MALFORMED`; the parser's historical private fallback must not qualify it for the new predicate |
| Duplicate name/key, reserved name, or implicit-member collision | Existing structural refusal remains effective |
| Original supported declared sites | Existing success and access behavior unchanged |

The current `endpoint()` already returns `UNSUPPORTED_SOURCE_FORM` for some absent/non-part intermediate traversals. This review does **not** require changing that separate historical behavior. Likewise, this phase does not require a general derived-property observer, an initializer validator, or coverage of every H16 alternative.

## Code observations and design decision

At the inspected revision, `Source.site()` combines absent and non-site members in one `MALFORMED` guard. Moving existence and external-access checks ahead of a narrow parameter/type predicate directly addresses the defect. The proposed exact token-pair check prevents a prefix match from admitting a wrong type.

`scan_class()` currently records an omitted parameter visibility as private. Keeping a separate authored-visibility field solely for the new predicate is justified and avoids changing unrelated legacy defaults. The parameter grammar has mandatory visibility, so omission cannot be evidence of a valid unsupported form.

No mandatory defect was identified in this proposed design, and no material scope expansion is needed. Exact implementation, test and preservation evidence remain to be reviewed.

## Required exact-candidate evidence

Candidate approval requires the exact commit/tree or otherwise fully bound bytes; the unchanged C270 source/oracle/failure identities; source-to-binding-to-comparison refusal propagation with retained reasons and input identities; no partial qualified results; the concrete negative distinctions above; unchanged existing supported results; and a closed C265→C266→C267→C268 dependency-pin chain. Relevant complete regression outcomes must be tied to the candidate implementation, fixtures, commands and environment. Failures and unrun roles remain explicit.

Full reads completed for AGENTS, GOAL, ROLE, PROTOCOL, HANDOFF, ontokin-delivery, OK-ENG-006, C260 CONTRACT/CONTROL-PLAN, and the named C270 control/finding/next-task records. Relevant core specification sections, construction sections 1/3.1/3.2, the full construction grammar, and the frozen source pair were inspected. No nested AGENTS files were found under the relevant repository directories. `design-read-identities.json` records the source file sizes and hashes; it is an identity record, not a claim that unrelated sections of the large language specifications were reread in full.

This review establishes no full H16, H20, H22, H24, C260, product, source-validity, site/world, native, model, or comparative qualification.
