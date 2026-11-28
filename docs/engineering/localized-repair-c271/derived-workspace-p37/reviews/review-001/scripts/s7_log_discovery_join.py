"""W3 (C271-P37 S7): the routine's started tests at C joined with C's discovery (MC28's second half, for an ordinary run).

Reads the Director's collector output of the unit log and MH's discovery document, both bound by SHA-256,
and lists every discovered ID that did not start and every started ID that was not discovered, with the order.

Usage: python3 -I -S -B s7_log_discovery_join.py LOCAL OUTPUT
"""
import hashlib
import json
import os
import sys

COLLECT = ("c271-p37/routine/ordinary-001.collect.json", "43fb549d98135ea42e09803d9e82e0dae6477471c758fcb535632aa76b2943cf")
DISCOVERY = ("c271-p37/routine/discovery-c.json", "51ca04483cd60fea967575d9f8c5164b4b713282cafcbcfe59df9fcbd12fd08b")


def bound(local, item):
    raw = open(os.path.join(local, item[0]), "rb").read()
    if hashlib.sha256(raw).hexdigest() != item[1]:
        raise SystemExit("input differs from its recorded digest: " + item[0])
    return json.loads(raw)


def main(local, output):
    collect, discovery = bound(local, COLLECT), bound(local, DISCOVERY)
    ids = discovery["ids_in_discovery_order"]
    started = [row["id"] for row in collect["tests"]]
    sequence = [raw_id for _, raw_id in sorted((run["order"], row["id"]) for row in collect["tests"] for run in row["runs"])]
    out = {"schema": "w3.c271-p37.log-discovery-join/1", "collect_sha256": COLLECT[1], "discovery_sha256": DISCOVERY[1],
           "discovered": len(ids), "started": len(started), "started_once_each": len(sequence) == len(set(sequence)),
           "started_not_discovered": sorted(set(started) - set(ids)),
           "discovered_not_started": sorted(set(ids) - set(started)),
           "start_order_equals_discovery_order_without_the_not_started": sequence == [i for i in ids if i in set(started)],
           "fixtures": [(row["id"], row["outcome"]) for row in collect["fixtures"]]}
    with open(output, "x", encoding="utf-8") as stream:
        json.dump(out, stream, indent=1, sort_keys=True)
        stream.write("\n")


if __name__ == "__main__":
    main(*sys.argv[1:3])
