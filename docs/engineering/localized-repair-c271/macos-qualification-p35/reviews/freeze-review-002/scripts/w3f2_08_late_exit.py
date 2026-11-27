"""Freeze review 002, script 08: a synthetic command for the timer test t3.

It stands for a wrapper: after DELAY seconds it writes the exit file <OUT>/timer-test/t3.exit.txt by exclusive
creation, then exits 0. It starts no process. Run in the background in the same message as the t3 timer.

Run: <worktree>/.venv/bin/python -I -S -B w3f2_08_late_exit.py DELAY
"""
import json
import os
import sys
import time

PROCESS_EVENTS = {"subprocess.Popen", "os.posix_spawn", "os.exec", "os.fork", "os.forkpty", "os.spawn", "os.system"}


def refuse(event, args):
    if event in PROCESS_EVENTS:
        raise PermissionError("no process: " + event)


sys.addaudithook(refuse)
PATH = "<local>/c271-p35/workers/W3-freeze-002/timer-test/t3.exit.txt"
t0 = time.time()
time.sleep(float(sys.argv[1]))
fd = os.open(PATH, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
os.write(fd, b"0\n")
os.close(fd)
t1 = time.time()
print(json.dumps({"started_epoch": t0, "exit_file_written_epoch": t1, "pid": os.getpid(), "pgrp": os.getpgrp(),
                  "sid": os.getsid(0)}))
