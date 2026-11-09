"""Install the pinned renderer modules into a new viewer-only three/ directory."""
import argparse
import base64
import hashlib
from io import BytesIO
from pathlib import Path
import tarfile
from urllib.request import urlopen

URL = "https://registry.npmjs.org/three/-/three-0.186.1.tgz"
SHA512 = "blFeqb49wRCSGUGj7gtpfnSGHy2lwDk94RhUmS1c/hTby70kvChbWpkJ4Pm1390LqzzvTmzgXKHPEafJwCb8jA=="
MODULES = (
    "LICENSE", "package.json", "build/three.core.js", "build/three.webgpu.js", "build/three.tsl.js",
    "build/three.module.js", "examples/jsm/controls/OrbitControls.js", "examples/jsm/gpgpu/CountingSort.js",
    "examples/jsm/loaders/GLTFLoader.js", "examples/jsm/loaders/GLTFGaussianSplatLoaderExtension.js",
    "examples/jsm/objects/GaussianSplat.js", "examples/jsm/utils/BufferGeometryUtils.js",
    "examples/jsm/utils/GaussianSplatUtils.js", "examples/jsm/utils/SkeletonUtils.js",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path, help="unused output path, normally the preview's three/ directory")
    parser.add_argument("--archive", type=Path, help="use this copy of the pinned npm tarball offline")
    args = parser.parse_args()
    with (args.archive.open("rb") if args.archive else urlopen(URL, timeout=30)) as stream:
        data = stream.read(6 * 1024 * 1024)
    if base64.b64encode(hashlib.sha512(data).digest()).decode() != SHA512:
        parser.exit(1, "Three.js tarball integrity mismatch\n")
    args.destination.mkdir(parents=True)
    with tarfile.open(fileobj=BytesIO(data), mode="r:gz") as archive:
        for filename in MODULES:
            output = args.destination / filename
            output.parent.mkdir(exist_ok=True, parents=True)
            with archive.extractfile("package/" + filename) as source:
                output.write_bytes(source.read())


if __name__ == "__main__":
    main()
