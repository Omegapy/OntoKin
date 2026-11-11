"""Fixed controls; never a native Blender worker or receiving implementation."""
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


case = sys.argv[1]
if case in {"L01", "L08"}:
    Path("stub-result.json").write_text('{"passed":true}')
elif case == "L02":
    Path("partial.bin").write_bytes(b"partial")
    sys.exit(17)
elif case in {"L03", "L04"}:
    while True:
        time.sleep(0.05)
elif case == "L05":
    child = subprocess.Popen([sys.executable, "-IBS", "-c",
        "import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(20)"])
    Path("grandchild.json").write_text(json.dumps({"pid": child.pid}))
    while True:
        time.sleep(0.05)
elif case == "L06":
    for _ in range(100):
        os.write(1, b"x" * 65536)
elif case == "L07":
    Path("stub-result.json").write_text('{"passed":')
else:
    raise ValueError("Unassigned lifecycle control")
