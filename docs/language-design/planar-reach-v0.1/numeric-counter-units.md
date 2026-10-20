# Numerical counter units: Draft 2 clarification D25

Document: **OK-LANG-006, Draft 2 numerical counter clarification**, version `0.1.0-draft.2`, October 20, 2026. Status: **proposed for adoption**.

This clarification fixes the counting-unit interpretation of the series limit in [numeric-admission.md](numeric-admission.md). Its limit remains 12,000. The exact pre-rollback version of this clarification is preserved in published checkpoint `1431e5f006ed73578afa3c1c08115a8502979d71`, with SHA-256 `fffe0a36c4e0292b6f02b690249488daddc1f1332f3eebecf3cd6ebfefa08194`. The older numerical checker, certificate and review bytes were not recovered; their historical results stay bound to those missing identities. The reconstructed files receive new hashes and fresh review. This provenance correction changes no numerical limit or counting unit, adopts no proposal and implements no runtime accounting.

## Effective counting unit

The unit is a **series recurrence step**:

| Calculation | One charged series recurrence step |
| --- | --- |
| Arctangent series | One iteration that adds one arctangent series term. |
| Paired sine/cosine series | One iteration that updates both the sine recurrence and the cosine recurrence and adds their respective terms. |

The maximum is **12,000 series recurrence steps per admission**, accumulated across all precision passes without resetting the counter. This is the existing behavior of `Budget.term()` at the arctangent and paired sine/cosine loops in [interval_oracle.py](interval_oracle.py).

The checker's historical `MAX_SERIES_TERMS` constant, `max_series_terms` budget argument and `series_terms` counters name this unit. The certificate fields `per_admission_series_terms` and `maximum_observed_series_terms_per_case` also count series recurrence steps. A sine/cosine pair is therefore one step in these historical fields, although that step updates two polynomial terms.

## Interval and inherited work charges

Every constituent outward interval operation within a recurrence step still receives its own interval-operation charge. The **100,000 interval-operation cap per admission** continues to apply across all passes, and those operations consume the program's inherited remaining semantic-work budget. One series-step charge does not replace, combine or waive the constituent interval-operation charges.

The production implementation must also count or conservatively precharge exact-rational classification, algebraic signs, rounding, integer-square-root work and other work required by the original numerical admission contract. A lower request budget may stop admission earlier. The standalone mathematical checker records its declared series and interval counters; the inherited runtime accounting and cancellation implementation remains a separate obligation.

All numerical maxima, precision passes, interval arithmetic, remainder bounds, rounding-cell obligations and original predetermined target values retain their specified meaning. Fresh reconstructed evidence must independently establish those obligations and record its actual measured counts; it cannot inherit the missing checker's results. This clarification resolves the counting unit before adoption.
