# First independent execution

The original script executed 193 controls against implementation SHA-256 `81024db4373a5a8dbfbf11bc2c0d711a91da7ce75459134b1619aa3a252b8cb8`. It reported 44 assertion failures, all caused by one reviewer assumption: the `origins` dictionary was required to have exactly the eight joint field keys. The implementation also provides accurate `limitLow` and `limitHigh` component pointers, which the agreed interface does not prohibit.

This is a reviewer test defect, not a product defect. The corrected expectation requires every joint-field pointer and separately verifies the optional component pointers. Original report, log, implementation bytes and reviewer script remain retained here. No failing expectation about numerical values or structural refusals is weakened.
