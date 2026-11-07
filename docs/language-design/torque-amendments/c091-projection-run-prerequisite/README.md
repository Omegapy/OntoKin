# C091 timed projection resource setup correction

R13 attempts a timed `inspect` after a constructed-only create, which has no program run. The inherited service correctly rejects this before the intended torque projection stage. This narrow amendment adds one real evaluate-prefix setup request at the same time and passes its actual returned run ID to the unchanged inspect. The original failure and all frozen bytes remain preserved.

The author and coordinator each reproduced the precondition using all 170 exact C090 package files, observing the original rejection and successful timed inspection only after a real evaluate request. Independent review and exact published byte/mode readback must pass before an overlaid resource run is authoritative.
