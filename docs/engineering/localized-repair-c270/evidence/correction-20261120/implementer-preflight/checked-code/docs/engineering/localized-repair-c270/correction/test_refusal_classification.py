"""Supplementary implementer controls for the C270 refusal correction.

Expectations come from the adopted member/type/access rules and C260 section
3.3, not from an evaluator. The independent frozen C270 control remains the
primary private-SiteRef oracle. These controls exercise nearby invalid forms
and refusal propagation through the three public interfaces.
"""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
ENGINEERING = ROOT / "docs/engineering"
PROOF = ENGINEERING / "semantic-export-c210/evidence/proof"
ORIGINALS = {
    "before.main.ok": "73c95c6509363e492084d7b6959356fe1955f4e78086a72b507167a271a33123",
    "hinges.ok": "1516e53179a7b9deecf593ab48afdcd72fba8124ea77868327c25a28a654681a",
    "before.glb": "d009d9dba6c69bb8e8e6decdfa9d7e1e92f819e3b59013d481cd30101c973534",
}
PARTIAL_FIELDS = {
    "records", "hinges", "sites", "objects", "hingeCount", "siteCount", "objectCount",
    "inputBindingVerified", "hingeComparisonVerified", "hingeSetAgreementVerified",
    "endpointAgreementVerified", "qualified",
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def load(name, relative):
    spec = importlib.util.spec_from_file_location(name, ENGINEERING / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


SOURCE = load("c270_correction_source", "localized-repair-c265/source_hinges.py")
BINDING = load("c270_correction_binding", "localized-repair-c266/hinge_binding.py")
COMPARISON = load("c270_correction_comparison", "localized-repair-c267/hinge_compare.py")


class RefusalClassification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        originals = {name: (PROOF / name).read_bytes() for name in ORIGINALS}
        for name, raw in originals.items():
            if digest(raw) != ORIGINALS[name]:
                raise AssertionError("Changed original input: " + name)
        cls.original_main = originals["before.main.ok"]
        cls.original_library = originals["hinges.ok"]
        cls.artifact = originals["before.glb"]

    def supplied(self, *, endpoint, field="parent", declaration=None, external=False):
        library = self.original_library
        if declaration is not None:
            marker = b'private class Blade @ "blade" {\n' if external else b'    public joint flex @ "flex": hinge {'
            replacement = marker + b"    " + declaration + b"\n" if external else b"    " + declaration + b"\n" + marker
            self.assertEqual(library.count(marker), 1)
            library = library.replace(marker, replacement)
        previous = b"self.pivot" if field == "parent" else b"self.blade.base"
        assignment = field.encode() + b" = " + previous + b";"
        self.assertEqual(library.count(assignment), 1)
        library = library.replace(assignment, field.encode() + b" = " + endpoint + b";")
        pin = ORIGINALS["hinges.ok"].encode()
        self.assertEqual(self.original_main.count(pin), 1)
        main = self.original_main.replace(pin, digest(library).encode())
        return {"main.ok": main, "hinges.ok": library}

    def assert_refusal(self, files, expected):
        hashes = {name: digest(raw) for name, raw in files.items()}
        sizes = {name: len(raw) for name, raw in files.items()}
        original = None
        for module, function, arguments, depth in (
            (SOURCE, "observe_source_hinges", (files,), 1),
            (BINDING, "bind_hinge_inputs", (files, self.artifact), 2),
            (COMPARISON, "compare_hinges", (files, self.artifact), 3),
        ):
            with self.subTest(interface=function, source_hashes=hashes):
                with self.assertRaises(module.Fault) as caught:
                    getattr(module, function)(*arguments)
                fault = caught.exception
                self.assertEqual(fault.code, expected)
                self.assertIsInstance(fault.detail, str)
                self.assertTrue(fault.detail)
                self.assertEqual(fault.sourceHashes, hashes)
                self.assertEqual(fault.sourceBytes, sizes)
                signature = fault.code, fault.detail, fault.origin
                if original is None:
                    original = signature
                self.assertEqual(signature, original)
                if depth > 1:
                    self.assertEqual(fault.artifactSha256, digest(self.artifact))
                    self.assertEqual(fault.artifactBytes, len(self.artifact))
                chain = []
                while fault is not None:
                    chain.append(fault)
                    self.assertFalse(PARTIAL_FIELDS & vars(fault).keys())
                    self.assertEqual((fault.code, fault.detail, fault.origin), original)
                    self.assertEqual(fault.sourceHashes, hashes)
                    self.assertEqual(fault.sourceBytes, sizes)
                    fault = fault.__cause__
                self.assertEqual(len(chain), depth)
                if depth > 1:
                    self.assertEqual(type(chain[-1]).__module__, "_c266_pinned_source")

    def test_missing_terminal_stays_malformed(self):
        for field, endpoint in (("parent", b"self.absent"), ("child", b"self.blade.absent")):
            with self.subTest(endpoint=endpoint):
                self.assert_refusal(self.supplied(field=field, endpoint=endpoint), "MALFORMED")

    def test_non_siteref_parameters_stay_malformed(self):
        for endpoint in (b"self.length", b"self.parent_frame"):
            with self.subTest(endpoint=endpoint):
                self.assert_refusal(self.supplied(endpoint=endpoint), "MALFORMED")

    def test_other_member_kinds_stay_malformed(self):
        for endpoint in (b"self.blade", b"self.flex", b"self.bend_to"):
            with self.subTest(endpoint=endpoint):
                self.assert_refusal(self.supplied(endpoint=endpoint), "MALFORMED")

    def test_invalid_nominal_type_forms_stay_malformed(self):
        for type_text in (b"SiteRef<Real>", b"mech.SiteRef", b'"SiteRef"', b"SiteRef SiteRef", b"Ref<SiteRef>"):
            with self.subTest(type_text=type_text):
                declaration = b'private param endpoint_ref @ "endpoint-ref": ' + type_text + b" = self.pivot;"
                self.assert_refusal(self.supplied(endpoint=b"self.endpoint_ref", declaration=declaration), "MALFORMED")

    def test_missing_property_visibility_stays_malformed(self):
        declaration = b'param endpoint_ref @ "endpoint-ref": SiteRef = self.pivot;'
        self.assert_refusal(self.supplied(endpoint=b"self.endpoint_ref", declaration=declaration), "MALFORMED")

    def test_public_own_siteref_is_unsupported(self):
        declaration = b'public param endpoint_ref @ "endpoint-ref": SiteRef = self.pivot;'
        self.assert_refusal(self.supplied(endpoint=b"self.endpoint_ref", declaration=declaration), "UNSUPPORTED_SOURCE_FORM")

    def test_public_external_siteref_is_unsupported_after_parent_site(self):
        declaration = b'public param endpoint_ref @ "endpoint-ref": SiteRef = self.base;'
        files = self.supplied(field="child", endpoint=b"self.blade.endpoint_ref", declaration=declaration, external=True)
        self.assert_refusal(files, "UNSUPPORTED_SOURCE_FORM")

    def test_private_external_siteref_stays_malformed(self):
        declaration = b'private param endpoint_ref @ "endpoint-ref": SiteRef = self.base;'
        files = self.supplied(field="child", endpoint=b"self.blade.endpoint_ref", declaration=declaration, external=True)
        self.assert_refusal(files, "MALFORMED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
