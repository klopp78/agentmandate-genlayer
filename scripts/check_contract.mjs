import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const source = readFileSync(resolve("contracts", "agent_mandate.py"), "utf8");

for (const required of [
  "class AgentMandate",
  "create_mandate",
  "request_action_authorization",
  "pause_mandate",
  "rotate_agent",
  "get_mandate",
  "get_receipt",
  "get_execution",
  "get_receipt_execution",
  "get_mandate_receipts",
  "get_evidence_pack",
  "get_latest_mandate_id",
  "get_latest_receipt_id",
  "get_latest_execution_id",
  "mand_",
  "rcpt_",
  "exec_",
  "caller_is_not_bound_agent",
  "evidence_commitment",
  "required_escalation",
  "risk_policy_hash",
  "gl.vm.run_nondet_unsafe",
  "gl.nondet.web.render",
  "execute_authorized_action",
  "receipt_does_not_authorize_execution",
  "execution_payload_not_receipt_bound",
  "execution_spend_not_receipt_bound",
  "evidence_requires_two_independent_https_sources",
]) {
  if (!source.includes(required)) {
    throw new Error(`missing required control: ${required}`);
  }
}

console.log("AgentMandate contract structure check passed");
