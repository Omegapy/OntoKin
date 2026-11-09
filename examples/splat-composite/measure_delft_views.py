"""Measure the same gold cart face in matched site-on/site-off frames from verify_delft_view.cjs."""
import argparse
import json
from pathlib import Path
from PIL import Image


def measure(directory):
    phases = ("early", "middle", "late")
    # C177's exact gold front-face colour on its pinned renderer.
    swatch = (200, 177, 86)
    rows = {}
    for phase in phases:
        with Image.open(directory / f"{phase}-off.png") as off, Image.open(directory / f"{phase}-on.png") as on:
            if off.size != on.size:
                raise ValueError("Site-on and site-off dimensions differ")
            pairs = zip(off.convert("RGB").getdata(), on.convert("RGB").getdata())
            reference = visible = changed = 0
            for a, b in pairs:
                changed += a != b
                if a == swatch:
                    reference += 1
                    visible += b == swatch
            if reference < 500:
                raise ValueError(f"{phase} has insufficient gold cart pixels ({reference})")
            rows[phase] = {"referenceCartPixels": reference, "retainedCartPixels": visible,
                           "retainedFraction": visible / reference, "changedCanvasPixels": changed}
    fractions = [rows[p]["retainedFraction"] for p in phases]
    return {"metric": "Exact gold pixels on the cart front face retained at the same locations "
                      "when the captured environment is switched on at a fixed time and camera.",
            "rgb": swatch, "posesSeconds": {"early": 1.08, "middle": 1.294, "late": 1.8},
            "results": rows, "behindPartialFrontThresholds": [0.15, 0.99],
            "behindPartialFrontPassed": fractions[0] < .15 and .15 < fractions[1] < .99 and fractions[2] > .99}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("captures", type=Path)
    args = parser.parse_args()
    if (args.captures / "views.json").is_file():
        data = json.loads((args.captures / "views.json").read_text())
        rows = {}
        for view in data["cameraButtons"]:
            rows[view] = {}
            for phase in data["posesSeconds"]:
                base = args.captures / f"{view}-{phase}"
                with (Image.open(str(base) + "-off.png") as off, Image.open(str(base) + "-on.png") as on,
                      Image.open(str(base) + "-site.png") as site):
                    if on.size != off.size or site.size != off.size:
                        raise ValueError("Mismatched dimensions")
                    triples = zip(off.convert("RGB").getdata(), on.convert("RGB").getdata(),
                                  site.convert("RGB").getdata())
                    count = exact = near = signal = zero_signal = 0
                    differences = []
                    for a, b, site_color in triples:
                        r, g, blue = a
                        # Gold cart surfaces have a different R:G ratio from the orange gatepost.
                        if g < 60 or not (1.08*g <= r <= 1.21*g and 1.8*blue <= g <= 2.35*blue):
                            continue
                        count += 1
                        diff = max(abs(x-y) for x,y in zip(a,b))
                        exact += diff == 0
                        near += diff <= 12
                        contrast = max(abs(x-y) for x,y in zip(b,site_color))
                        signal += contrast > 12
                        zero_signal += contrast == 0
                        differences.append(contrast)
                if count < 300:
                    rows[view][phase] = {"qualified": False, "referenceGoldPixels": count,
                                         "reason": "Fewer than 300 source-only gold pixels"}
                    continue
                rows[view][phase] = {"qualified": True, "referenceGoldPixels": count, "exactRgb": exact,
                    "within12PerChannel": near, "within12Fraction": near / count,
                    "distinctFromSiteByMoreThan12": signal, "distinctFraction": signal / count,
                    "identicalToSiteOnly": zero_signal,
                    "medianContrastWithSiteOnly": sorted(differences)[count//2]}
        report = {"metric": "Count source-only gold cart pixels, then measure RGB change at those same "
                  "pixels with the real captured environment enabled. The near-match cutoff is 12 in "
                  "each 8-bit colour channel. Also compare composite with captured-site-only colour at "
                  "those pixels. Contrast over 12 in at least one channel counts as a distinct cart "
                  "pixel. Background colour similarity affects this metric. It does not measure physical opacity.",
                  "posesSeconds": data["posesSeconds"], "results": rows}
    else:
        report = measure(args.captures)
    print(json.dumps(report, indent=2))
