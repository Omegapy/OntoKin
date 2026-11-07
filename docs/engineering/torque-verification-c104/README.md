# C104 · Complete driver runs and the original A08 deadline

The inherited driver executed all 34 roles on the packaged torque revision, then all 34 again after a verification-only correction. The first run had 33 passing roles and the second had 33. The overall unit role is failed. The original run passed each of the 3,988 individually identified legacy tests from C088. All 16 cases requiring external evidence remain open.

The driver had omitted the installed-package initializer and the two split license notices from its isolated working copy. The correction adds the three inputs to verification and introduces a Git-backed regression test. All 22 local-driver tests passed. The corrected isolated checkout contained all 12,500 tracked paths.

The unit failures had two causes. The original A08 program requests 30 seconds of processing and failed during recording export and readback, before 13 artifact-read methods could start. C104's separately identified 80-second A08 produced the C096 recording byte for byte in 36.588 seconds, using 452,627 operations. All 13 configured read-method controls passed on the fresh store. Missing Pillow caused 36 native-reader errors across ten methods. In a clean verification environment with Pillow 13.0.0 installed, all eleven methods and 47 subtests passed.

Of 724 frozen world-rate fields, 673 matched bit for bit and 51 differed. The candidate matched the previously adopted implementation's observations, interval endpoints and allowances at every one of the 362 requests. All 1,444 vectors met their exact interval bounds. This conclusion applies to the enumerated requests.

The installed wheel passed the original six torque cases on CPython 3.11.17 and 3.13.16 for Linux x86-64. On each interpreter, three GLBs matched C102 and three requests reproduced their original resource-limit refusals. A separate two-crash recovery test restored 12 byte receipts using independently persisted evidence and rejected a missing receipt.

The request for an independent human playback result is open. On a paired 80-second fixture, pose sampling took 18.396 seconds, certificate construction 10.185 seconds, independent validation 7.508 seconds and encoding 0.978 seconds. The next engineering step is a bounded experiment inside frame sampling, retaining the original A08 source, independent proof and work checks. Then run the original test class and full driver with all verification dependencies installed. [Recorded results](results.json) · [Owned scope](SCOPE.md)
