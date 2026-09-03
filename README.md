# AgentMandate for GenLayer

AgentMandate is a GenLayer-native authorization layer for autonomous AI agents.
A human creates an enforceable mandate with permitted scope, spending limits,
required evidence, escalation rules, and an emergency pause path. A bound agent
then asks the contract whether a proposed action is allowed. GenLayer validators
evaluate the action against the mandate and write a durable consensus receipt.

- Contract: `0x4b035a6808cFf701AbfFE47c6E989Cf371E8ff36`
- Explorer: https://explorer-studio.genlayer.com/address/0x4b035a6808cFf701AbfFE47c6E989Cf371E8ff36
- Source: https://github.com/klopp78/agentmandate-genlayer

## Product flow

1. Connect a Studio wallet in the web app.
2. Create a `mand_*` mandate. For demo use, the app can bind the connected
   wallet as the agent wallet.
3. Submit an agent action with type, requested action, declared cost, evidence
   URLs, and execution context.
4. Validators return `approve`, `reject`, or `review` with risk level,
   escalation requirement, reason, mandate hash, and action hash.
5. Read the exact mandate, receipt timeline, and exportable evidence pack from
   contract storage.

The frontend does not compute local verdicts. It uses `genlayer-js` for writes
and reads, and displays the contract response returned by Studionet.

## Contract design

`contracts/agent_mandate.py` implements:

- Persistent mandate registry: `create_mandate`, `get_mandate`,
  `list_mandate_ids`
- Agent lifecycle controls: `rotate_agent`, `pause_mandate`
- Consensus authorization: `request_action_authorization`
- Contract-generated IDs: `mand_*` and `rcpt_*`
- Receipt history: `get_mandate_receipts`, `get_receipt`,
  `list_receipt_ids`
- Evidence export: `get_evidence_pack`

Validators independently recompute the decision, mandate hash, action hash, and
escalation flag before accepting the write.

## Verification

```powershell
python scripts/check_contract.py
npm run build
```
