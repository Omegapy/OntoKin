"""Run the model side of a serial operator session. The caller supplies a confined worker and a budget gate."""
import json
import re
from time import monotonic

RULES = """You are working alone in a disposable Linux workspace. Complete the assigned task using the files and installed tools in this workspace. Keep the starting files and put your final editable source, outputs, report and rebuild instructions under submission/. Store working notes in the workspace if needed.
On each turn return exactly one fenced block. Use a sh block to run shell commands in the worker. When the files are complete, reply with SUBMIT on its own line to finish. For example,
```sh
pwd
```
Commands run in fresh shells in the same working directory and share files. Their output and exit status will be provided in the next turn. You may retry failed commands. You can use local files and programs and the loopback viewer. All tool and model calls share a time and token limit."""
ACTION = re.compile(r"(?m)^```(sh|bash|final)[ \t]*\r?\n(.*?)\r?\n```[ \t]*(?:\r?\n|$)", re.DOTALL)


def clip(text, limit):
    if len(text) <= limit:
        return text
    half = limit // 2
    return text[:half] + "\n[Middle omitted by the controller. Use a narrower file range or query.]\n" + text[-half:]


def run(gate, client, snapshot, guest_tool, log):
    """guest_tool invokes only the confined command transport via the same gate."""
    history = []
    started = monotonic()
    turn = 0
    first = guest_tool(gate, "cat participant/task.md && printf '\\n' && cat BUILD.md && printf '\\n' && ls -1")
    log('initialTaskRead', receipt=first)
    if first['exit'] or first.get('stdoutTruncated') or first.get('truncated'):
        raise ValueError('Cannot read the assigned task')
    assigned = first['stdout']
    while True:
        turn += 1
        previous = "\n\n".join(history)
        prompt = RULES + "\n\nAssigned task, build instructions and available files:\n" + assigned + ("\n\nRecent transcript:\n" + clip(previous, 18000) if previous else "")
        reply, usage = gate.infer(client, prompt, snapshot, 1024)
        text = reply['text']
        log('modelTurn', turn=turn, seconds=monotonic() - started, reply=text, usage=usage)
        if text.strip() == "SUBMIT":
            log('submitted', turn=turn, seconds=monotonic() - started, response=text)
            return text
        match = ACTION.search(text)
        if not match:
            feedback = "Return a fenced sh command or reply SUBMIT."
            history.append("Your response:\n" + text + "\nController:\n" + feedback)
            log("formatRejected", turn=turn, message=feedback)
            continue
        kind, body = match.groups()
        if text[match.end():].strip():
            log('additionalTextIgnored', turn=turn)
        if kind == "final":
            log('submitted', turn=turn, seconds=monotonic() - started, response=body)
            return body
        receipt = guest_tool(gate, body)
        log('guestResult', turn=turn, receipt=receipt)
        history.append("Your command:\n" + body + "\nWorker result:\n" + clip(
            json.dumps(receipt, ensure_ascii=False), 8000))
