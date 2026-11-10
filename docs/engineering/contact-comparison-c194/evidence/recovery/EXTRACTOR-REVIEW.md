# C194 evidence extractor review

The extractor passes code review and thirteen behavioral controls. Its SHA-256 is `5b1add438e12ace2d8d23d748b81b6d10c50f2588399dea6de79cd765e5879ed`.

A valid three-archive fixture produced exactly its three expected payload files and a completion receipt. Twelve invalid inputs were refused: archive checksum mismatch, manifest checksum mismatch, payload-content mismatch, path traversal, symbolic link, hard link, FIFO, duplicate tar member, duplicate JSON key, file/directory collision, output inside the source repository and an already existing output directory.

No failed test published a partial output, wrote outside the temporary destination, or altered the pre-existing sentinel. Temporary staging directories were removed after failure.

The code fixes the permitted root mapping, checks the exact archive inventory and file identities, copies only regular bytes into exclusively created files, and publishes a new destination only after all archives verify. It uses no native solver, author, receiving, network or Git commands.

These controls ran on Linux with Python 3.12.14. The actual evidence extraction and composed recorded replay remain separate final package checks. EXTRACTOR-REVIEW.json contains every observed outcome.
