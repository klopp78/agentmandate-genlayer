# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
"""Consensus-gated execution mandates for autonomous AI agents."""

from genlayer import *
import hashlib
import json


class AgentMandate(gl.Contract):
    """Mandates, independently verified evidence receipts, and gated executions."""

    mandate_count: u64
    receipt_count: u64
    execution_count: u64
    mandate_ids: DynArray[str]
    receipt_ids: DynArray[str]
    execution_ids: DynArray[str]
    mandates: TreeMap[str, str]
    mandate_owners: TreeMap[str, str]
    mandate_agents: TreeMap[str, str]
    receipts: TreeMap[str, str]
    executions: TreeMap[str, str]
    mandate_receipts: TreeMap[str, str]
    receipt_executions: TreeMap[str, str]

    def __init__(self):
        self.mandate_count = u64(0)
        self.receipt_count = u64(0)
        self.execution_count = u64(0)

    @gl.public.view
    def get_mandate(self, mandate_id: str) -> str:
        return self.mandates.get(mandate_id, "")

    @gl.public.view
    def get_receipt(self, receipt_id: str) -> str:
        return self.receipts.get(receipt_id, "")

    @gl.public.view
    def get_execution(self, execution_id: str) -> str:
        return self.executions.get(execution_id, "")

    @gl.public.view
    def get_receipt_execution(self, receipt_id: str) -> str:
        return self.receipt_executions.get(receipt_id, "")

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
    def list_execution_ids(self) -> str:
        return json.dumps([item for item in self.execution_ids], separators=(",", ":"))

    @gl.public.view
    def get_latest_mandate_id(self) -> str:
        return _latest(self.mandate_ids)

    @gl.public.view
    def get_latest_receipt_id(self) -> str:
        return _latest(self.receipt_ids)

    @gl.public.view
    def get_latest_execution_id(self) -> str:
        return _latest(self.execution_ids)

    @gl.public.view
    def get_evidence_pack(self, receipt_id: str) -> str:
        receipt = _load_json(self.receipts.get(receipt_id, ""), "unknown_receipt")
        mandate = _load_json(self.mandates.get(receipt["mandate_id"], ""), "unknown_mandate")
        return _dump({
            "schema_version": "agentmandate.evidence.v2",
            "receipt": receipt,
            "mandate": {
                "mandate_id": mandate["mandate_id"],
                "version": mandate["version"],
                "status": mandate["status"],
                "owner": mandate["owner"],
                "agent_wallet": mandate["agent_wallet"],
                "max_spend_units": mandate["max_spend_units"],
                "mandate_hash": mandate["mandate_hash"],
                "risk_policy_hash": mandate["risk_policy_hash"],
                "evidence_policy_hash": mandate["evidence_policy_hash"],
            },
            "verified_source_manifest": receipt["verified_source_manifest"],
            "accepted_write_sequence": receipt["sequence"],
            "contract_generated_ids": {"mandate_id": receipt["mandate_id"], "receipt_id": receipt["receipt_id"]},
        })

    @gl.public.write
    def create_mandate(self, title: str, mandate_text: str, permitted_scope: str, max_spend_units: str, evidence_requirements: str, escalation_rules: str, agent_wallet: str) -> str:
        title = _require_text(title, "invalid_title", 4, 80)
        mandate_text = _require_text(mandate_text, "invalid_mandate_text", 80, 5000)
        permitted_scope = _require_text(permitted_scope, "invalid_scope", 20, 2000)
        evidence_requirements = _require_text(evidence_requirements, "invalid_evidence_requirements", 20, 2000)
        escalation_rules = _require_text(escalation_rules, "invalid_escalation_rules", 20, 2000)
        spend_cap = _units(max_spend_units, "invalid_spend_cap")
        owner, agent = _wallet(gl.message.sender_address), _wallet(agent_wallet)
        self.mandate_count = u64(int(self.mandate_count) + 1)
        mandate_id = "mand_" + _sha256(owner + "|" + title + "|" + str(self.mandate_count))[:20]
        risk_policy = permitted_scope + "|" + str(spend_cap) + "|" + escalation_rules
        record = {
            "schema_version": "agentmandate.v2", "mandate_id": mandate_id, "version": 1, "status": "active", "title": title,
            "mandate_text": mandate_text, "permitted_scope": permitted_scope, "max_spend_units": spend_cap,
            "evidence_requirements": evidence_requirements, "escalation_rules": escalation_rules, "owner": owner, "agent_wallet": agent,
            "mandate_hash": _sha256(mandate_text), "risk_policy_hash": _sha256(risk_policy),
            "evidence_policy_hash": _sha256(evidence_requirements + "|" + escalation_rules), "created_sequence": int(self.mandate_count),
        }
        self.mandates[mandate_id] = _dump(record)
        self.mandate_owners[mandate_id], self.mandate_agents[mandate_id] = owner, agent
        self.mandate_receipts[mandate_id] = "[]"
        self.mandate_ids.append(mandate_id)
        return mandate_id

    @gl.public.write
    def pause_mandate(self, mandate_id: str) -> str:
        _require_owner(self, mandate_id)
        mandate = _load_mandate(self, mandate_id)
        mandate["status"], mandate["version"] = "paused", int(mandate["version"]) + 1
        self.mandates[mandate_id] = _dump(mandate)
        return mandate_id

    @gl.public.write
    def rotate_agent(self, mandate_id: str, agent_wallet: str) -> str:
        _require_owner(self, mandate_id)
        mandate = _load_mandate(self, mandate_id)
        if mandate["status"] != "active":
            raise Exception("mandate_not_active")
        agent = _wallet(agent_wallet)
        mandate["agent_wallet"], mandate["version"] = agent, int(mandate["version"]) + 1
        self.mandate_agents[mandate_id], self.mandates[mandate_id] = agent, _dump(mandate)
        return mandate_id

    @gl.public.write
    def request_action_authorization(self, mandate_id: str, action_type: str, execution_payload: str, evidence_urls_csv: str, declared_spend_units: str, execution_context: str) -> str:
        mandate = _load_mandate(self, mandate_id)
        caller = _wallet(gl.message.sender_address)
        if mandate["status"] != "active":
            raise Exception("mandate_not_active")
        if caller != self.mandate_agents.get(mandate_id, ""):
            raise Exception("caller_is_not_bound_agent")
        action_type = _canonical_slug(action_type, "invalid_action_type")
        execution_payload = _require_text(execution_payload, "invalid_execution_payload", 20, 3000)
        spend_units = _units(declared_spend_units, "invalid_declared_spend")
        if spend_units > int(mandate["max_spend_units"]):
            raise Exception("spend_exceeds_mandate_cap")
        execution_context = _require_text(execution_context, "invalid_execution_context", 0, 3000)
        evidence_urls = _canonical_urls(evidence_urls_csv)
        action_hash = _sha256(mandate_id + "|" + str(mandate["version"]) + "|" + action_type + "|" + execution_payload + "|" + str(spend_units) + "|" + execution_context + "|" + ",".join(evidence_urls))

        def leader_fn():
            return _assess(mandate, action_type, execution_payload, evidence_urls, spend_units, execution_context, action_hash)

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return):
                return False
            try:
                proposed = _parse_decision(leader_result.calldata)
                independent = _parse_decision(_assess(mandate, action_type, execution_payload, evidence_urls, spend_units, execution_context, action_hash))
            except Exception:
                return False
            return proposed["decision"] == independent["decision"] and proposed["action_hash"] == independent["action_hash"] and proposed["mandate_hash"] == independent["mandate_hash"] and proposed["evidence_bundle_hash"] == independent["evidence_bundle_hash"] and proposed["verified_source_count"] == independent["verified_source_count"] and proposed["required_escalation"] == independent["required_escalation"] and abs(int(proposed["confidence"]) - int(independent["confidence"])) <= 15

        result = _parse_decision(gl.vm.run_nondet_unsafe(leader_fn, validator_fn))
        self.receipt_count = u64(int(self.receipt_count) + 1)
        receipt_id = "rcpt_" + _sha256(action_hash + "|" + str(self.receipt_count))[:20]
        result.update({
            "schema_version": "agentmandate.receipt.v2", "receipt_id": receipt_id, "mandate_id": mandate_id,
            "mandate_version": int(mandate["version"]), "action_type": action_type, "execution_payload_hash": _sha256(execution_payload),
            "declared_spend_units": spend_units, "evidence_urls": evidence_urls, "evidence_commitment": _sha256(",".join(evidence_urls)),
            "execution_context_hash": _sha256(execution_context), "requested_by": caller, "sequence": int(self.receipt_count), "execution_status": "unexecuted",
        })
        self.receipts[receipt_id] = _dump(result)
        self.receipt_ids.append(receipt_id)
        history = json.loads(self.mandate_receipts.get(mandate_id, "[]"))
        history.append(receipt_id)
        self.mandate_receipts[mandate_id] = json.dumps(history, separators=(",", ":"))
        return receipt_id

    @gl.public.write
    def execute_authorized_action(self, receipt_id: str, execution_payload: str, spend_units: str, execution_reference: str) -> str:
        """The only execution path: consumes one approving receipt with exact payload and spend."""
        receipt = _load_json(self.receipts.get(receipt_id, ""), "unknown_receipt")
        mandate = _load_mandate(self, receipt["mandate_id"])
        caller = _wallet(gl.message.sender_address)
        if mandate["status"] != "active":
            raise Exception("mandate_not_active")
        if caller != self.mandate_agents.get(receipt["mandate_id"], ""):
            raise Exception("caller_is_not_bound_agent")
        if receipt["decision"] != "approve" or bool(receipt["required_escalation"]):
            raise Exception("receipt_does_not_authorize_execution")
        if receipt["execution_status"] != "unexecuted" or self.receipt_executions.get(receipt_id, ""):
            raise Exception("receipt_already_consumed")
        payload, reference = _require_text(execution_payload, "invalid_execution_payload", 20, 3000), _require_text(execution_reference, "invalid_execution_reference", 8, 300)
        exact_spend = _units(spend_units, "invalid_execution_spend")
        if _sha256(payload) != receipt["execution_payload_hash"]:
            raise Exception("execution_payload_not_receipt_bound")
        if exact_spend != int(receipt["declared_spend_units"]):
            raise Exception("execution_spend_not_receipt_bound")
        if exact_spend > int(mandate["max_spend_units"]):
            raise Exception("execution_spend_exceeds_mandate_cap")
        self.execution_count = u64(int(self.execution_count) + 1)
        execution_id = "exec_" + _sha256(receipt_id + "|" + reference + "|" + str(self.execution_count))[:20]
        execution = {
            "schema_version": "agentmandate.execution.v2", "execution_id": execution_id, "receipt_id": receipt_id,
            "mandate_id": receipt["mandate_id"], "action_hash": receipt["action_hash"], "execution_payload_hash": receipt["execution_payload_hash"],
            "spend_units": exact_spend, "execution_reference": reference, "executed_by": caller, "sequence": int(self.execution_count),
        }
        receipt["execution_status"], receipt["execution_id"] = "executed", execution_id
        self.receipts[receipt_id] = _dump(receipt)
        self.executions[execution_id], self.receipt_executions[receipt_id] = _dump(execution), execution_id
        self.execution_ids.append(execution_id)
        return execution_id


def _assess(mandate: dict, action_type: str, payload: str, urls: list, spend_units: int, context: str, action_hash: str) -> str:
    sources = _verified_sources(urls)
    evidence_bundle_hash = _sha256(_dump(sources))
    prompt = f"""
You are a GenLayer validator deciding whether an AI agent may execute a proposed action.
The public evidence below was fetched independently by this validator. Use only the supplied snapshots.
Approve only when the action is within scope, spend is within cap, and the diverse sources substantiate the request.
Use review for ambiguity or insufficient evidence, reject for violations.
Mandate: {json.dumps(mandate)}
Action type: {action_type}
Execution payload: {payload}
Declared spend units: {spend_units}
Execution context: {context}
Verified evidence snapshots: {json.dumps(sources)}
Action hash: {action_hash}
Return only minified JSON with exactly: decision (approve|reject|review), confidence (0-100), required_escalation (boolean), risk_level (low|medium|high|blocked), reason (under 420 chars), mandate_hash (exactly {mandate["mandate_hash"]}), action_hash (exactly {action_hash}), evidence_bundle_hash (exactly {evidence_bundle_hash}), verified_source_count (exactly {len(sources)}), verified_hosts (exactly {len({item["host"] for item in sources})}), verified_source_manifest (exactly {json.dumps(sources)}).
"""
    result = json.loads(gl.nondet.exec_prompt(prompt))
    if str(result.get("mandate_hash", "")) != mandate["mandate_hash"] or str(result.get("action_hash", "")) != action_hash or str(result.get("evidence_bundle_hash", "")) != evidence_bundle_hash:
        raise Exception("validator_commitment_mismatch")
    # Preserve the concrete sources fetched by this validator, not an LLM retelling of them.
    result["verified_source_manifest"] = sources
    return _dump(result)


def _verified_sources(urls: list) -> list:
    sources = []
    for index, url in enumerate(urls):
        text = gl.nondet.web.render(url, mode="text")[:5000]
        normalized = " ".join(text.split())
        if len(normalized) < 80:
            raise Exception("evidence_snapshot_too_short")
        sources.append({"source_index": index + 1, "url": url, "url_hash": _sha256(url), "host": _host(url), "snapshot_hash": _sha256(normalized), "excerpt": normalized[:700]})
    return sources


def _parse_decision(raw: str) -> dict:
    result = json.loads(raw)
    if result.get("decision") not in ("approve", "reject", "review"):
        raise Exception("invalid_decision")
    confidence = int(result.get("confidence", -1))
    if confidence < 0 or confidence > 100 or result.get("risk_level") not in ("low", "medium", "high", "blocked"):
        raise Exception("invalid_decision_fields")
    if len(str(result.get("reason", ""))) == 0 or len(str(result.get("reason", ""))) > 420:
        raise Exception("invalid_reason")
    if len(str(result.get("mandate_hash", ""))) != 64 or len(str(result.get("action_hash", ""))) != 64 or len(str(result.get("evidence_bundle_hash", ""))) != 64:
        raise Exception("invalid_commitment")
    count, hosts = int(result.get("verified_source_count", -1)), int(result.get("verified_hosts", -1))
    manifest = result.get("verified_source_manifest", [])
    if count < 2 or count > 4 or hosts < 2 or hosts > count or len(manifest) != count:
        raise Exception("invalid_verified_sources")
    return {"decision": result["decision"], "confidence": confidence, "required_escalation": bool(result.get("required_escalation", False)), "risk_level": result["risk_level"], "reason": str(result["reason"]), "mandate_hash": str(result["mandate_hash"]), "action_hash": str(result["action_hash"]), "evidence_bundle_hash": str(result["evidence_bundle_hash"]), "verified_source_count": count, "verified_hosts": hosts, "verified_source_manifest": manifest}


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
    urls, seen, hosts = [], set(), set()
    for value in str(raw).split(","):
        url = value.strip()
        key = url.rstrip("/").lower()
        if len(url) == 0:
            continue
        if not url.startswith("https://") or len(url) > 500 or key in seen:
            raise Exception("invalid_evidence_url")
        seen.add(key)
        urls.append(url)
        hosts.add(_host(url))
    if len(urls) < 2 or len(urls) > 4 or len(hosts) < 2:
        raise Exception("evidence_requires_two_independent_https_sources")
    return urls


def _host(url: str) -> str:
    host = url.split("//", 1)[1].split("/", 1)[0].lower()
    if not host or "." not in host:
        raise Exception("invalid_evidence_host")
    return host


def _units(raw: str, error: str) -> int:
    value = str(raw).strip()
    if not value.isdigit() or len(value) > 12:
        raise Exception(error)
    units = int(value)
    if units < 0 or units > 1000000000:
        raise Exception(error)
    return units


def _canonical_slug(raw: str, error: str) -> str:
    value = str(raw).strip().lower()
    if len(value) < 3 or len(value) > 40 or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789_-" for char in value):
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


def _dump(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _latest(values: DynArray[str]) -> str:
    return "" if len(values) == 0 else values[len(values) - 1]
