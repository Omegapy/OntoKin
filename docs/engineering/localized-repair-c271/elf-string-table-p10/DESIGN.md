# Finite dynamic string-table mapping

The P09 reader requires the whole dynamic string table to fit inside one file-backed `PT_LOAD` segment. The retained Python image crosses two adjacent segments. This correction changes only how those table bytes are assembled. ELF target files are read as data and never executed.

Partition the half-open virtual range `[DT_STRTAB, DT_STRTAB + DT_STRSZ)` at each intersecting file-backed load-segment start and end. For each nonempty interval, collect the file offset implied by every segment covering that entire interval. Exactly one distinct offset is required. Read the interval through the existing bounded `read` function and concatenate the pieces in virtual-address order.

Every load-segment mapping has slope one: `file_offset + address - virtual_start`. Therefore equality at the interval start establishes the same mapping throughout that interval. Identical or partially coincident mappings keep their existing acceptance. Conflicting offsets are ambiguous even when a larger segment covers the whole table; a gap or a memory-only tail supplies no file-backed offset and is refused. Adjacent virtual intervals can have separated file offsets. Empty intersections add no interval.

The existing maximum of 256 program headers bounds the number of cut points. The existing 4 MiB string-table limit bounds total assembled bytes; individual reads retain the 16 MiB/file-size and short-read guards. The supplied callback runs while collecting cuts and before each interval/read, preserving deadline and cancellation failure propagation. No callback exception is suppressed.

The correction does not change dynamic-table mapping, header/segment validation, allowed dynamic tags/flags, metadata uniqueness, string offsets/termination/ASCII, needed-library and search-path rules, final file identity checks, or public result/error schemas. In particular, loader tokens such as `$ORIGIN` remain refused under the accepted contract. Mapping the retained Python bytes does not imply that every later guard accepts them.

Independent worker `/root/elf_review` reviewed this interval rule before production edits. Its frozen corpus and construction proof will bind exact expected metadata/refusals before execution. A separate permanent test module will consume a lossless encoding of those bytes; the original inspection tests remain byte-identical. The exact candidate and evidence require independent final review.

This finite reader does not implement a general dynamic loader or establish host qualification. H0/H1, Node/ldd, the original seven methods, complete routine and integration remain outside P10.
