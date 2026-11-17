# Original author failure

`before-initial.json` is the exact first CLI result on the frozen original
`before.main.ok`, `hinges.ok` and `before.glb` bytes listed in `INPUTS.json`.
The lexer rejected byte 872, the `^` in `0[m/s^2]`. The initial uncommitted
reader was not separately hashed. To reproduce the failure from reader commit
`055d1e83f33586e488a35961d29f405b2884beea`, remove `^` from the `LEXER` symbol
character class and run the before endpoint command. Do not change the proof
inputs. The correction added the symbol; it did not evaluate gravity.

The subsequent `before-attempt-02.json` and `after-attempt-02.json` are actual
bound comparison results from the corrected reader.
