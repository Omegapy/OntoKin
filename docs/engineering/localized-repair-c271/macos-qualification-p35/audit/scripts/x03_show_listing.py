"""W4 audit 001, exploration x03: print a listing's entries for one root up to a depth.

Usage: x03_show_listing.py LISTING.json ROOT MAXDEPTH [PREFIX]
"""
import json
import sys

listing = json.load(open(sys.argv[1]))
root = sys.argv[2]
maxdepth = int(sys.argv[3])
prefix = sys.argv[4] if len(sys.argv) > 4 else ""
entries = listing["roots"][root]["entries"]
for item in entries:
    path = item["path"]
    if prefix and not path.startswith(prefix):
        continue
    depth = 0 if path == "." else path.count("/") + 1
    if depth > maxdepth:
        continue
    extra = item.get("sha256", item.get("target", ""))
    print(f'{item.get("kind","?"):9} {item.get("mode",""):6} {item.get("size",""):>9} n{item.get("nlink","")} {path} {extra[:16] if extra else ""}')
