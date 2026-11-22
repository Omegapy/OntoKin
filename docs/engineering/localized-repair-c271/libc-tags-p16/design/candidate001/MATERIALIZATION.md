# Inert fixture materialization

The frozen manifest records every authored fixture as a regular file with mode `0o600`. No fixture has an executable mode. Source copies and author scripts are also evidence data; invoking an author script through an explicitly selected Python interpreter does not make the ELF data executable.

Git records content and executable-bit state, not the distinction between `0o600` and `0o644`. A later implementation phase must copy exact frozen fixture bytes to a fresh private directory, verify hash/size, and set only those owned copies to the recorded inert modes. It must never alter historical fixture bytes, change real image pins, or install/run a synthetic ELF. The archive/manifest is the exact mode authority for restoration; a checkout alone proves only the Git-supported mode state.

No operational Python, Node, loader or libc is materialized by this instruction. Logical operational descriptors in JSON are mocked boundary observations and remain distinct from the bytes/modes of these inert fixtures.
