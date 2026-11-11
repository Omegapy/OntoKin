# Actual-main identity correction

The first local import attempt of the verified GitHub merge refused its signed payload because the header reconstruction omitted the signature's final continuation line. No remote write was retried. Exact preserved payload plus signature later reproduced the actual SHA.

An orchestration error launched the intended main checks before requiring that import command to succeed. Those checks actually ran on clean local publication b8fb9b5ffbe4ec8ea40d325b47af27f31098c2b7, whose tree is exactly the observed merge tree. Their captured identity remains unchanged and their files are preserved as publication-confirmation-*; they are not labeled actual-main evidence. The actual-main cohort is run separately only after checkout and asserted equality with observed merge d952254d5e63602e6d11c696e62ae8965d57c78e.
