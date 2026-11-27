"""Replace this host's machine paths and account values by labels (used by my scripts' writers).

Labels come from the freeze's own places, longest first, plus the clone root and the account name
(the last component of <home>), so no private value is written into my outputs.
"""
import json, os


def labeller(freeze_path):
    places = json.load(open(freeze_path, "rb"))["places"]
    pairs = [(value.rstrip("/"), key) for key, value in places.items() if key.startswith("<") and isinstance(value, str)]
    worktree = places["<worktree>"]
    clone = os.path.join(os.path.dirname(os.path.dirname(worktree)), "OntoKin")
    pairs.append((clone, "<clone>"))
    pairs.append((os.path.dirname(places["<local>"]), "<volume-parent>"))
    pairs.append(("/" + "/".join(places["<local>"].strip("/").split("/")[:2]), "<volume>"))
    pairs.sort(key=lambda pair: -len(pair[0]))
    account = os.path.basename(places["<home>"])

    def label(text):
        for value, key in pairs:
            text = text.replace(value, key)
        return text.replace(account, "<user>")
    return label
