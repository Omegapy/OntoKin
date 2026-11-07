# C091 Agent cursor template correction

The A04 frozen workflow names `A04.page.result.next_cursor` twice, while the inherited Agent response supplies `A04.page.next_cursor`. Both the original attempted workflow and its unchanged inputs are preserved. The two exact changes in AMENDMENT.json correct only reference resolution; no product envelope, pagination, source, expectation, budget or tolerance changes. The frozen input remains byte-identical.

The author and coordinator each executed the supplied reproduction using all 170 exact C090 Python package files at `94a7796a54725ca764b2027deb43f09204f8a6de`. Each retained the actual create, first-page and successful next-page exchanges. A separate independent review and actual published readback are required before an overlaid workflow run becomes authoritative.
