# AgentMandate for GenLayer

## Agent Tank Studio Next build

AgentMandate is a GenLayer-native authorization layer for autonomous AI agents.
A human creates an enforceable mandate with permitted scope, spending limits,
required evidence, escalation rules, and an emergency pause path. A bound agent
then asks the contract whether a proposed action is allowed. GenLayer validators
evaluate the action against the mandate and write a durable consensus receipt.

This Agent Tank revision targets Studio Next:

- Network: Studio Next
- Chain ID: `61997`
- RPC: `https://studio-next.genlayer.com/api`
- Explorer: `https://explorer-studio-dev.genlayer.com/`
- SDK: `genlayer-js@2.0.0-rc.1`
- Transaction Kit: `@genlayer/transaction-kit@0.1.0-rc.2`

- Contract: `0x9177514caB55a30E2D43deF68C94a1D4a6A22b7b`
- Explorer: https://explorer-studio-dev.genlayer.com/address/0x9177514caB55a30E2D43deF68C94a1D4a6A22b7b
- Source: https://github.com/klopp78/agentmandate-genlayer

Replace the contract address after deploying a fresh Studio Next instance.

## Receipt-gated execution and verified evidence

AgentMandate does not treat a verdict as an informational log. A bound agent can
call `execute_authorized_action` only with a one-time `approve` receipt, the
exact payload and spend amount committed in that receipt, and an active mandate.
Replayed receipts, `review` or `reject` verdicts, escalations, altered payloads,
and altered spend amounts all fail on-chain.

Before a receipt is written, every validator independently renders two to four
distinct HTTPS sources with `gl.nondet.web.render`. The receipt stores the
committed URL, host, URL hash, snapshot hash, excerpt, and evidence-bundle hash
that informed consensus.

## Product flow

1. Connect a Studio wallet in the web app.
2. Create a `mand_*` mandate. For demo use, the app can bind the connected
   wallet as the agent wallet.
3. Submit an agent action with type, exact execution payload, declared spend,
   two to four independent HTTPS evidence URLs, and execution context.
4. Validators return `approve`, `reject`, or `review` with risk level,
   escalation requirement, reason, mandate hash, action hash, fetched source
   manifest, host diversity, and evidence-bundle hash.
5. Execute only by consuming an approving `rcpt_*` receipt with the exact
   payload hash and spend amount committed in the receipt.
6. Read the exact mandate, receipt timeline, execution record, and exportable
   evidence pack from contract storage.

The frontend does not compute local verdicts. It uses `genlayer-js` for writes
and reads, and displays the contract response returned by Studionet.

## Contract design

`contracts/agent_mandate.py` implements:

- Persistent mandate registry: `create_mandate`, `get_mandate`,
  `list_mandate_ids`
- Agent lifecycle controls: `rotate_agent`, `pause_mandate`
- Consensus authorization: `request_action_authorization`
- Receipt-gated execution: `execute_authorized_action`
- Contract-generated IDs: `mand_*`, `rcpt_*`, and `exec_*`
- Receipt history: `get_mandate_receipts`, `get_receipt`,
  `list_receipt_ids`
- Verified evidence: validators fetch independent HTTPS sources with
  `gl.nondet.web.render` and store URL hashes, hosts, snapshot hashes, excerpts,
  and an evidence-bundle hash
- Evidence export: `get_evidence_pack`

Validators independently recompute the decision, mandate hash, action hash,
evidence-bundle hash, source count, host diversity, and escalation flag before
accepting the write.

## Verification

```powershell
python scripts/check_contract.py
npm run build
```

## Portal checklist

- Submit as an Agent Tank project, not a normal static listing.
- Use the Studio Next explorer contract URL from the fresh deployment.
- Include the GitHub repository URL.
- Include a demo video URL. For Agent Tank the video is mandatory even if the
  Portal field says optional.
- In the description, state that the frontend calls the deployed contract and
  does not compute local allow or deny results.
