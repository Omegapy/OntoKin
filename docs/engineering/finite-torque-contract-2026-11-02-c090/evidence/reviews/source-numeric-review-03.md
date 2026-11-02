# Independent source and numerical review 03

**Outcome: approved scoped clarification.** The current specification SHA-256 is `1df5fe712760d3e0af6614f6fbd200708bae76a1191e1aa5829dff8382e74ced`. Its entire text equals the previously approved `f46327fb246c904f584e5d8ae1a42c5962e43d8cff073ee5530a20d7ef531050` version with exactly the single replacement preserved in `source-token-clarification-01.json`.

The inherited lexer reserves `using`; the bundled-source lexer additionally reserves `for`. The amended wording correctly preserves their existing roles and says only that the torque production gives them an additional torque-specific interpretation. It does not introduce a global reserved name or make either token an ordinary identifier. The EBNF hash remains `01818c3ad1c6d1bb703a8ae8cb42c3ed88dc6ce40be1c37b1e7971424b0f26fc`.

No numerical, staging, error-transport, work-charge or diagnostic rule changed. Review 02 and its independent 1,121 arithmetic checks therefore remain applicable; no redundant mathematical or runtime run was performed. The accompanying JSON records the exact inherited lexer hashes and scope limits.
