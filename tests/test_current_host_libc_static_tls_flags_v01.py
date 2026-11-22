"""Execute the unchanged P17 flags controls through the shared libc adapter.

The archive contains synthetic metadata and explicitly mocked observations.
Passing these controls does not qualify actual host inputs or a runtime plan.
"""

import unittest

import test_current_host_libc_plt_metadata_v01 as shared


CORPUS = shared.FrozenCorpus(
    phase="p17",
    archive_relative=(
        "docs/engineering/localized-repair-c271/"
        "libc-flags-p17/design/CANDIDATE001.zip"
    ),
    archive_sha256=(
        "d59d4d71a9f73065a000ae3de8233beb82ad5a33a3b526de93debb845f0d86c4"
    ),
    manifest_sha256=(
        "5561dcd3cf718362f0716bb0c3ebf7fcf273befa1f6348f9996331d151b7c89b"
    ),
    expectations_sha256=(
        "9ec492d20fe2184414d818fca3ff37bcfdf1a20416dcb042d0bc2667456c9bd8"
    ),
    fixtures_sha256=(
        "d2a5f2388ee5cfba67b4be3e7d1e10744c374faf727dc89e65f1fbf3508ef797"
    ),
    case_count=41,
)


class LibcStaticTlsFrozenTests(shared.FrozenLibcCaseMixin, unittest.TestCase):
    """Bind each original P17 case to its literal expectation and input bytes."""

    corpus = CORPUS


shared.install_cases(LibcStaticTlsFrozenTests)


if __name__ == "__main__":
    unittest.main()
