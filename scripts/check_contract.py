import ast
import pathlib

source = (pathlib.Path(__file__).resolve().parents[1] / "contracts" / "agent_mandate.py").read_text(encoding="utf-8")
ast.parse(source)

for required in (
    "class AgentMandate",
    "create_mandate",
    "request_action_authorization",
    "pause_mandate",
    "rotate_agent",
    "get_mandate",
    "get_receipt",
    "get_mandate_receipts",
    "get_evidence_pack",
    "get_latest_mandate_id",
    "get_latest_receipt_id",
    "mand_",
    "rcpt_",
    "caller_is_not_bound_agent",
    "evidence_commitment",
    "required_escalation",
    "risk_policy_hash",
    "gl.vm.run_nondet_unsafe",
):
    if required not in source:
        raise SystemExit(f"missing required control: {required}")

print("AgentMandate contract structure check passed")
