# C271 P10: bounded ELF string-table mapping correction

This phase addresses P09's inability to map a dynamic string table across adjacent ELF load segments. ELF is the executable file format; this reader inspects bytes without executing the image.

The [phase](PHASE.json) and [session](../../../workflow/tasks/C271/P10-SESSION.md) retain acceptance and stopping conditions. [Early recovery](EARLY-RECOVERY-RECEIPT.json) is independently accepted and saved. The independent oracle precedes implementation. Expected results are not derived from candidate output.

Only finite file mapping is selected. Host qualification, Node/ldd, the original seven tests, complete routine, integration and parent completion remain later gates. Historical P09 and all earlier failed evidence remain unchanged.
