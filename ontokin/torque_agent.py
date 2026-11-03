"""Durable .22 finite torque, scoped source repairs and recorded delivery."""
from .torque_program_runtime import TorqueProgramRuntime
from .torque_protocol import TorqueProtocol, SCHEMA_VERSION
from .torque_store import TorqueProgramStore
from .texture_agent import TextureAgentService


class TorqueAgentService(TextureAgentService):
    protocol_type = TorqueProtocol
    runtime_type = TorqueProgramRuntime
    store_type = TorqueProgramStore

    def __init__(self, store_path, *, protocol=SCHEMA_VERSION, **kwargs):
        super().__init__(store_path, protocol=protocol, **kwargs)

    @property
    def _verified_artifact(self):
        from .torque_artifacts import verified_artifact
        return verified_artifact(self)

    def close(self):
        try:
            super().close()
        finally:
            from .torque_artifacts import clear_verified_artifact
            clear_verified_artifact(self)

    def _read_artifact(self, task):
        from .torque_artifacts import read_retained_artifact
        return read_retained_artifact(self, task)

    def _check_task_response(self, task):
        # Failed/cancelled receipts retain the exact inherited cleanup path.
        if task.response["status"] != "succeeded" or getattr(task, "bounded_failure", False):
            return super()._check_task_response(task)
        from .agent_protocol import ProtocolError
        from .diagnostics import OntoKinError
        from .json_limits import JSONLimitError
        from .torque_json_limits import measure_response_json
        check = getattr(task, "execution_check", None)
        if check is not None:
            task.response["execution_budget"] = check.report(task.response["status"])
        ledger = check.execution_budget
        ledger.stage = "publication"
        try:
            measure_response_json(task.response,
                max_entries=task.request.get("budgets", {}).get("max_value_entries", 100000),
                check=ledger.tick)
            ledger.checkpoint()
            task.response["execution_budget"] = check.report(task.response["status"])
        except (OntoKinError, JSONLimitError) as error:
            details = error.diagnostic.details if isinstance(error, OntoKinError) else error.details
            raise ProtocolError("OKL-E-RESOURCE", "The complete result exceeded its shared request allowance; no effects committed.",
                                **details, effects_committed=False) from error

    @staticmethod
    def catalog(**kwargs):
        from .torque_agent_catalog import catalog
        return catalog(**kwargs)
