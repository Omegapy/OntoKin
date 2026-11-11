"""Diagnostics for the separately selected static-tray destination."""

PROFILE = "ontokin.static-tray/0.1.0"
CONTRACT = "OK-MAP-STATIC-TRAY-001/0.1.0"


class TrayError(ValueError):
    def __init__(self, code, message, *, stage="mapping", pointer="", candidate=None,
                 details=None, findings=None):
        super().__init__(message)
        self.code = code if code.startswith("OTRAY-") else "OTRAY-E-" + code
        self.stage = stage
        self.pointer = pointer
        self.candidate = candidate
        self.details = details or {}
        self.findings = findings or []

    def to_dict(self):
        return {"code": self.code, "message": str(self), "stage": self.stage,
                "pointer": self.pointer, "candidate_identity": self.candidate,
                "profile": PROFILE, "contract": CONTRACT, "details": self.details,
                "findings": self.findings}
