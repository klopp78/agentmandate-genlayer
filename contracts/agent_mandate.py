# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""Consensus authorization mandates for autonomous AI agents."""

from genlayer import *
import hashlib
import json


class AgentMandate(gl.Contract):
    """Append-only mandate and receipt ledger for agent actions."""

    mandate_count: u64
    receipt_count: u64
    mandate_ids: DynArray[str]
    receipt_ids: DynArray[str]
    mandates: TreeMap[str, str]
    mandate_owners: TreeMap[str, str]
    mandate_agents: TreeMap[str, str]
    receipts: TreeMap[str, str]
    mandate_receipts: TreeMap[str, str]

    def __init__(self):
        self.mandate_count = u64(0)
        self.receipt_count = u64(0)

    @gl.public.view
    def get_mandate(self, mandate_id: str) -> str:
        return self.mandates.get(mandate_id, "")

    @gl.public.view
    def get_receipt(self, receipt_id: str) -> str:
        return self.receipts.get(receipt_id, "")

    @gl.public.view
    def get_mandate_receipts(self, mandate_id: str) -> str:
        return self.mandate_receipts.get(mandate_id, "[]")

    @gl.public.view
    def list_mandate_ids(self) -> str:
        return json.dumps([item for item in self.mandate_ids], separators=(",", ":"))

    @gl.public.view
    def list_receipt_ids(self) -> str:
        return json.dumps([item for item in self.receipt_ids], separators=(",", ":"))

    @gl.public.view
    def get_latest_mandate_id(self) -> str:
        if len(self.mandate_ids) == 0:
            return ""
        return self.mandate_ids[len(self.mandate_ids) - 1]

    @gl.public.view
    def get_latest_receipt_id(self) -> str:
        if len(self.receipt_ids) == 0:
            return ""
        return self.receipt_ids[len(self.receipt_ids) - 1]

    @gl.public.view
    def get_evidence_pack(self, receipt_id: str) -> str:
        receipt = _load_json(self.receipts.get(receipt_id, ""), "unknown_receipt")
        mandate = _load_json(self.mandates.get(receipt["mandate_id"], ""), "unknown_mandate")
        return json.dumps({
            "schema_version": "agentmandate.evidence.v1",
            "receipt": receipt,
            "mandate": {
                "mandate_id": mandate["mandate_id"],
                "version": mandate["version"],
                "title": mandate["title"],
                "status": mandate["status"],
                "owner": mandate["owner"],
                "agent_wallet": mandate["agent_wallet"],
                "mandate_hash": mandate["mandate_hash"],
                "risk_policy_hash": mandate["risk_policy_hash"],
                "evidence_policy_hash": mandate["evidence_policy_hash"],
            },
            "accepted_write_sequence": receipt["sequence"],
            "contract_generated_ids": {
                "mandate_id": receipt["mandate_id"],
                "receipt_id": receipt["receipt_id"],
            },
        }, sort_keys=True, separators=(",", ":"))

    @gl.public.write
    def create_mandate(
        self,
        title: str,
        mandate_text: str,
        permitted_scope: str,
        spending_limit: str,
        evidence_requirements: str,
        escalation_rules: str,
        agent_wallet: str,
    ) -> str:
        title = _require_text(title, "invalid_title", 4, 80)
        mandate_text = _require_text(mandate_text, "invalid_mandate_text", 80, 5000)
        permitted_scope = _require_text(permitted_scope, "invalid_scope", 20, 2000)
        spending_limit = _require_text(spending_limit, "invalid_spending_limit", 2, 400)
        evidence_requirements = _require_text(evidence_requirements, "invalid_evidence_requirements", 20, 2000)
        escalation_rules = _require_text(escalation_rules, "invalid_escalation_rules", 20, 2000)
        owner = _wallet(gl.message.sender_address)
        agent = _wallet(agent_wallet)

        self.mandate_count = u64(int(self.mandate_count) + 1)
        mandate_id = "mand_" + _sha256(owner + "|" + title + "|" + str(self.mandate_count))[:20]
        risk_policy = permitted_scope + "\n" + spending_limit + "\n" + escalation_rules
        evidence_policy = evidence_requirements + "\n" + escalation_rules
        record = {
            "schema_version": "agentmandate.v1",
            "mandate_id": mandate_id,
            "version": 1,
            "status": "active",
            "title": title,
            "mandate_text": mandate_text,
            "permitted_scope": permitted_scope,
            "spending_limit": spending_limit,
            "evidence_requirements": evidence_requirements,
            "escalation_rules": escalation_rules,
            "owner": owner,
            "agent_wallet": agent,
            "mandate_hash": _sha256(mandate_text),
            "risk_policy_hash": _sha256(risk_policy),
            "evidence_policy_hash": _sha256(evidence_policy),
            "created_sequence": int(self.mandate_count),
        }
        self.mandates[mandate_id] = _dump(record)
        self.mandate_owners[mandate_id] = owner
        self.mandate_agents[mandate_id] = agent
        self.mandate_receipts[mandate_id] = "[]"
        self.mandate_ids.append(mandate_id)
        return mandate_id

    @gl.public.write
    def pause_mandate(self, mandate_id: str) -> str:
        _require_owner(self, mandate_id)
        mandate = _load_mandate(self, mandate_id)
        mandate["status"] = "paused"
        mandate["version"] = int(mandate["version"]) + 1
        self.mandates[mandate_id] = _dump(mandate)
        return mandate_id

    @gl.public.write
    def rotate_agent(self, mandate_id: str, agent_wallet: str) -> str:
        _require_owner(self, mandate_id)
        mandate = _load_mandate(self, mandate_id)
        if mandate["status"] != "active":
            raise Exception("mandate_not_active")
        agent = _wallet(agent_wallet)
        mandate["agent_wallet"] = agent
        mandate["version"] = int(mandate["version"]) + 1
        self.mandate_agents[mandate_id] = agent
        self.mandates[mandate_id] = _dump(mandate)
        return mandate_id

    @gl.public.write
    def request_action_authorization(
        self,
        mandate_id: str,
        action_type: str,
        requested_action: str,
        evidence_urls_csv: str,
        declared_cost: str,
        execution_context: str,
    ) -> str:
        mandate = _load_mandate(self, mandate_id)
        caller = _wallet(gl.message.sender_address)
        if mandate["status"] != "active":
            raise Exception("mandate_not_active")
        if caller != self.mandate_agents.get(mandate_id, ""):
            raise Exception("caller_is_not_bound_agent")
        action_type = _canonical_slug(action_type, "invalid_action_type")
        requested_action = _require_text(requested_action, "invalid_requested_action", 20, 3000)
        declared_cost = _require_text(declared_cost, "invalid_declared_cost", 1, 200)
        execution_context = _require_text(execution_context, "invalid_execution_context", 0, 3000)
        evidence_urls = _canonical_urls(evidence_urls_csv)
        action_hash = _sha256(mandate_id + "|" + str(mandate["version"]) + "|" + action_type + "|" + requested_action + "|" + declared_cost + "|" + execution_context + "|" + ",".join(evidence_urls))

        def leader_fn():
            return _judge(mandate, action_type, requested_action, evidence_urls, declared_cost, execution_context, action_hash)

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                proposed = _parse_decision(leader_result.calldata)
                independent = _parse_decision(_judge(mandate, action_type, requested_action, evidence_urls, declared_cost, execution_context, action_hash))
            except Exception:
                return False
            return proposed["decision"] == independent["decision"] and proposed["action_hash"] == independent["action_hash"] and proposed["mandate_hash"] == independent["mandate_hash"] and proposed["required_escalation"] == independent["required_escalation"] and abs(int(proposed["confidence"]) - int(independent["confidence"])) <= 20

        result = _parse_decision(gl.vm.run_nondet_unsafe(leader_fn, validator_fn))
        self.receipt_count = u64(int(self.receipt_count) + 1)
        receipt_id = "rcpt_" + _sha256(action_hash + "|" + str(self.receipt_count))[:20]
        result.update({
            "schema_version": "agentmandate.receipt.v1",
            "receipt_id": receipt_id,
            "mandate_id": mandate_id,
            "mandate_version": int(mandate["version"]),
            "action_type": action_type,
            "requested_action": requested_action,
            "declared_cost": declared_cost,
            "evidence_urls": evidence_urls,
            "evidence_commitment": _sha256(",".join(evidence_urls)),
            "execution_context_hash": _sha256(execution_context),
            "requested_by": caller,
            "sequence": int(self.receipt_count),
        })
        self.receipts[receipt_id] = _dump(result)
        self.receipt_ids.append(receipt_id)
        history = json.loads(self.mandate_receipts.get(mandate_id, "[]"))
        history.append(receipt_id)
        self.mandate_receipts[mandate_id] = json.dumps(history, separators=(",", ":"))
        return receipt_id


def _judge(mandate: dict, action_type: str, requested_action: str, evidence_urls: list, declared_cost: str, execution_context: str, action_hash: str) -> str:
    prompt = f"""
You are a GenLayer validator for AgentMandate. Decide if an autonomous AI agent may execute the requested action.
Approve only when the action fits the mandate, scope, spending limit, evidence requirements, and escalation rules.
Reject when it clearly violates them. Use review when evidence, spending, authority, or risk is ambiguous.

Mandate title: {mandate["title"]}
Mandate text: {mandate["mandate_text"]}
Permitted scope: {mandate["permitted_scope"]}
Spending limit: {mandate["spending_limit"]}
Evidence requirements: {mandate["evidence_requirements"]}
Escalation rules: {mandate["escalation_rules"]}
Mandate hash: {mandate["mandate_hash"]}

Action type: {action_type}
Requested action: {requested_action}
Declared cost: {declared_cost}
Evidence URLs: {json.dumps(evidence_urls)}
Execution context: {execution_context}
Action hash: {action_hash}

Return only minified JSON with exactly these keys:
decision: approve|reject|review
confidence: integer 0-100
required_escalation: true|false
risk_level: low|medium|high|blocked
reason: under 420 characters
mandate_hash: exactly {mandate["mandate_hash"]}
action_hash: exactly {action_hash}
Do not invent missing evidence. Treat missing required evidence as review or reject.
"""
    return _dump(json.loads(gl.nondet.exec_prompt(prompt)))


def _parse_decision(raw: str) -> dict:
    result = json.loads(raw)
    if result.get("decision") not in ("approve", "reject", "review"):
        raise Exception("invalid_decision")
    confidence = int(result.get("confidence", -1))
    if confidence < 0 or confidence > 100:
        raise Exception("invalid_confidence")
    if result.get("risk_level") not in ("low", "medium", "high", "blocked"):
        raise Exception("invalid_risk_level")
    reason = str(result.get("reason", ""))
    if len(reason) == 0 or len(reason) > 420:
        raise Exception("invalid_reason")
    if len(str(result.get("mandate_hash", ""))) != 64 or len(str(result.get("action_hash", ""))) != 64:
        raise Exception("invalid_commitment")
    return {"decision": result["decision"], "confidence": confidence, "required_escalation": bool(result.get("required_escalation", False)), "risk_level": result["risk_level"], "reason": reason, "mandate_hash": str(result["mandate_hash"]), "action_hash": str(result["action_hash"])}


def _load_mandate(contract: AgentMandate, mandate_id: str) -> dict:
    return _load_json(contract.mandates.get(mandate_id, ""), "unknown_mandate")


def _require_owner(contract: AgentMandate, mandate_id: str):
    if _wallet(gl.message.sender_address) != contract.mandate_owners.get(mandate_id, ""):
        raise Exception("caller_is_not_mandate_owner")


def _load_json(raw: str, error: str) -> dict:
    if len(raw) == 0:
        raise Exception(error)
    return json.loads(raw)


def _canonical_urls(raw: str) -> list:
    items = []
    for value in str(raw).split(","):
        url = value.strip()
        if len(url) == 0:
            continue
        if not (url.startswith("https://") or url.startswith("ipfs://")):
            raise Exception("invalid_evidence_url")
        if url not in items:
            items.append(url)
    if len(items) == 0 or len(items) > 6:
        raise Exception("invalid_evidence_count")
    return items


def _canonical_slug(raw: str, error: str) -> str:
    value = str(raw).strip().lower()
    if len(value) < 3 or len(value) > 40:
        raise Exception(error)
    if any(char not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for char in value):
        raise Exception(error)
    return value


def _require_text(raw: str, error: str, min_len: int, max_len: int) -> str:
    value = str(raw).strip()
    if len(value) < min_len or len(value) > max_len:
        raise Exception(error)
    return value


def _wallet(raw) -> str:
    value = str(raw).strip().lower()
    if not value.startswith("0x") or len(value) != 42:
        raise Exception("invalid_wallet")
    return value


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _dump(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))
