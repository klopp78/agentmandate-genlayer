"use client";

import { useEffect, useState } from "react";
import {
  AGENT_MANDATE_ADDRESS,
  readEvidencePack,
  readExecution,
  readLatestMandateId,
  readLatestExecutionId,
  readLatestReceiptId,
  readMandate,
  readMandateReceipts,
  readReceipt,
  writeAgentMandate,
  type WalletAddress,
} from "@/lib/genlayer";

declare global {
  interface Window { ethereum?: { request(args: { method: string }): Promise<unknown> } }
}

type Status = "ready" | "working" | "accepted" | "error";

const explorer = `https://explorer-studio.genlayer.com/address/${AGENT_MANDATE_ADDRESS}`;
const github = "https://github.com/klopp78/agentmandate-genlayer";
const asText = (value: unknown) => typeof value === "string" ? value : JSON.stringify(value, null, 2);

export default function Home() {
  const [wallet, setWallet] = useState<WalletAddress | null>(null);
  const [status, setStatus] = useState<Status>("ready");
  const [message, setMessage] = useState("Connect a Studio wallet to create an enforceable AI-agent mandate.");
  const [title, setTitle] = useState("Treasury Research Agent Mandate");
  const [mandateText, setMandateText] = useState("The agent may prepare public-market research, compare vendors, and draft small operational transactions. It must not transfer funds, sign contracts, publish external statements, access private accounts, or exceed the declared spending limit without explicit human escalation.");
  const [scope, setScope] = useState("Allowed scope: research public sources, prepare vendor shortlists, draft unsigned transactions, and request approval for operational actions linked to this mandate.");
  const [spendingLimit, setSpendingLimit] = useState("50");
  const [evidenceRules, setEvidenceRules] = useState("Each action must include two to four independent HTTPS evidence sources. Validators must fetch those sources, commit URL hashes, host names, snapshot hashes, and excerpts before a receipt can authorize execution.");
  const [escalationRules, setEscalationRules] = useState("Escalate to human review for fund transfers, legal commitments, missing evidence, new counterparties, policy conflicts, high-risk operations, or emergency pause conditions.");
  const [agentWallet, setAgentWallet] = useState("");
  const [mandateId, setMandateId] = useState("");
  const [actionType, setActionType] = useState("vendor_research");
  const [requestedAction, setRequestedAction] = useState("Compare three public API-monitoring vendors and prepare an unsigned recommendation memo. Do not make a purchase or bind the organization.");
  const [evidenceUrls, setEvidenceUrls] = useState("https://docs.genlayer.com, https://portal.genlayer.foundation/agent-tank/");
  const [declaredCost, setDeclaredCost] = useState("0");
  const [context, setContext] = useState("The requester needs a shortlist for uptime monitoring. No private credentials, payments, or production changes are involved.");
  const [receiptId, setReceiptId] = useState("");
  const [executionReference, setExecutionReference] = useState("demo-vendor-research-001");
  const [executionId, setExecutionId] = useState("");
  const [record, setRecord] = useState("");
  const [timeline, setTimeline] = useState("");
  const [pack, setPack] = useState("");

  useEffect(() => {
    if (wallet && !agentWallet) setAgentWallet(wallet);
  }, [wallet, agentWallet]);

  const fail = (error: unknown) => {
    setStatus("error");
    setMessage(error instanceof Error ? error.message : "The contract call did not complete.");
  };

  async function connect() {
    if (!window.ethereum) return fail("No browser wallet was detected.");
    try {
      setStatus("working");
      const accounts = await window.ethereum.request({ method: "eth_requestAccounts" }) as string[];
      if (!accounts[0]) throw new Error("Wallet did not return an account.");
      setWallet(accounts[0] as WalletAddress);
      setStatus("ready");
      setMessage("Wallet connected. For demo flow, this wallet is also used as the bound agent.");
    } catch (error) {
      fail(error);
    }
  }

  async function loadRecord(kind: "mandate" | "receipt", id: string) {
    const value = kind === "mandate" ? await readMandate(id, wallet ?? undefined) : await readReceipt(id, wallet ?? undefined);
    setRecord(asText(value));
  }

  async function createMandate() {
    if (!wallet) return fail("Connect a wallet before creating a mandate.");
    const agent = (agentWallet || wallet) as WalletAddress;
    try {
      setStatus("working");
      const { hash } = await writeAgentMandate(wallet, "create_mandate", [
        title, mandateText, scope, spendingLimit, evidenceRules, escalationRules, agent,
      ]);
      const id = String(await readLatestMandateId(wallet));
      setMandateId(id);
      await loadRecord("mandate", id);
      setStatus("accepted");
      setMessage(`create_mandate accepted; generated ID: ${id}. Transaction: ${hash}`);
    } catch (error) {
      fail(error);
    }
  }

  async function authorizeAction() {
    if (!wallet) return fail("Connect a wallet before requesting authorization.");
    if (!mandateId) return fail("Create or enter a mandate ID first.");
    try {
      setStatus("working");
      const { hash } = await writeAgentMandate(wallet, "request_action_authorization", [
        mandateId, actionType, requestedAction, evidenceUrls, declaredCost, context,
      ]);
      const id = String(await readLatestReceiptId(wallet));
      setReceiptId(id);
      await loadRecord("receipt", id);
      setStatus("accepted");
      setMessage(`request_action_authorization accepted; generated receipt: ${id}. Transaction: ${hash}`);
    } catch (error) {
      fail(error);
    }
  }

  async function executeAuthorizedAction() {
    if (!wallet) return fail("Connect a wallet before executing an authorized action.");
    if (!receiptId) return fail("Enter an approving receipt ID first.");
    try {
      setStatus("working");
      const { hash } = await writeAgentMandate(wallet, "execute_authorized_action", [
        receiptId, requestedAction, declaredCost, executionReference,
      ]);
      const id = String(await readLatestExecutionId(wallet));
      setExecutionId(id);
      const execution = await readExecution(id, wallet);
      setRecord(asText(execution));
      setStatus("accepted");
      setMessage(`Execution consumed receipt ${receiptId}; generated execution ID: ${id}. Transaction: ${hash}`);
    } catch (error) {
      fail(error);
    }
  }

  async function readTimeline() {
    if (!mandateId) return fail("Enter a mandate ID first.");
    try {
      setStatus("working");
      const value = await readMandateReceipts(mandateId, wallet ?? undefined);
      setTimeline(asText(value));
      setStatus("ready");
      setMessage(`Receipt timeline for ${mandateId} loaded from contract storage.`);
    } catch (error) {
      fail(error);
    }
  }

  async function readPack() {
    if (!receiptId) return fail("Enter a receipt ID first.");
    try {
      setStatus("working");
      const value = await readEvidencePack(receiptId, wallet ?? undefined);
      setPack(asText(value));
      setStatus("ready");
      setMessage(`Evidence pack for ${receiptId} loaded from contract storage.`);
    } catch (error) {
      fail(error);
    }
  }

  async function copyPack() {
    if (!pack) return fail("Load an evidence pack before copying it.");
    try {
      await navigator.clipboard.writeText(pack);
      setStatus("ready");
      setMessage("Evidence pack copied.");
    } catch (error) {
      fail(error);
    }
  }

  return (
    <main>
      <header>
        <div><span className="mark">AM</span><span className="eyebrow">Agent Tank Build</span></div>
        <button className="wallet" onClick={connect}>{wallet ? `${wallet.slice(0, 6)}...${wallet.slice(-4)}` : "Connect wallet"}</button>
      </header>

      <section className="intro">
        <p className="eyebrow">Consensus authorization for the agentic economy</p>
        <h1>AgentMandate</h1>
        <p>Create enforceable permission boundaries for AI agents, require validators to fetch the evidence behind a request, and execute only through one-time approving receipts.</p>
        <div className="links">
          <a href={explorer} target="_blank">Studio contract</a>
          <a href={github} target="_blank">Source code and tests</a>
        </div>
      </section>

      <section className="status" data-state={status}>
        <strong>{status === "working" ? "Working" : status === "accepted" ? "Accepted" : status === "error" ? "Needs attention" : "Ready"}</strong>
        <span>{message}</span>
      </section>

      <section className="workspace">
        <div className="panel mandate">
          <div className="panel-title"><span>01</span><h2>Create mandate</h2></div>
          <label>Mandate title<input value={title} onChange={(event) => setTitle(event.target.value)} /></label>
          <label>Bound agent wallet<input value={agentWallet} onChange={(event) => setAgentWallet(event.target.value)} placeholder="0x..." /></label>
          <label>Mandate text<textarea value={mandateText} onChange={(event) => setMandateText(event.target.value)} /></label>
          <label>Permitted scope<textarea value={scope} onChange={(event) => setScope(event.target.value)} /></label>
          <label>Maximum spend per execution (whole USDC units)<input value={spendingLimit} onChange={(event) => setSpendingLimit(event.target.value)} inputMode="numeric" /></label>
          <label>Evidence requirements<textarea value={evidenceRules} onChange={(event) => setEvidenceRules(event.target.value)} /></label>
          <label>Escalation and pause rules<textarea value={escalationRules} onChange={(event) => setEscalationRules(event.target.value)} /></label>
          <button onClick={createMandate}>Create mandate</button>
          <div className="divider" />
          <label>Contract-generated mandate ID<input value={mandateId} onChange={(event) => setMandateId(event.target.value)} placeholder="mand_..." /></label>
          <button className="secondary" onClick={() => loadRecord("mandate", mandateId)}>Read mandate</button>
        </div>

        <div className="panel">
          <div className="panel-title"><span>02</span><h2>Authorize action</h2></div>
          <label>Action type<input value={actionType} onChange={(event) => setActionType(event.target.value)} /></label>
          <label>Exact execution payload<textarea value={requestedAction} onChange={(event) => setRequestedAction(event.target.value)} /></label>
          <label>Evidence URLs, comma-separated (2+ independent HTTPS sources)<textarea value={evidenceUrls} onChange={(event) => setEvidenceUrls(event.target.value)} /></label>
          <label>Declared spend (whole USDC units)<input value={declaredCost} onChange={(event) => setDeclaredCost(event.target.value)} inputMode="numeric" /></label>
          <label>Execution context<textarea value={context} onChange={(event) => setContext(event.target.value)} /></label>
          <button onClick={authorizeAction}>Request consensus authorization</button>
          <div className="divider" />
          <label>Contract-generated receipt ID<input value={receiptId} onChange={(event) => setReceiptId(event.target.value)} placeholder="rcpt_..." /></label>
          <div className="actions">
            <button className="secondary" onClick={() => loadRecord("receipt", receiptId)}>Read receipt</button>
            <button className="secondary" onClick={readTimeline}>Read timeline</button>
          </div>
          <div className="divider" />
          <label>Execution reference<input value={executionReference} onChange={(event) => setExecutionReference(event.target.value)} /></label>
          <button onClick={executeAuthorizedAction}>Execute authorized action</button>
          <label>Contract-generated execution ID<input value={executionId} onChange={(event) => setExecutionId(event.target.value)} placeholder="exec_..." /></label>
          <button className="secondary" onClick={() => readExecution(executionId, wallet ?? undefined).then((value) => setRecord(asText(value))).catch(fail)}>Read execution</button>
        </div>

        <aside className="record">
          <div className="panel-title"><span>Ledger</span><h2>Contract record</h2></div>
          <p>The app reads mandate, receipt, and execution records directly from GenLayer contract storage. It does not calculate local allow or deny results.</p>
          <pre>{record || "No record loaded yet."}</pre>
          <ul>
            <li>Persistent mandate registry with owner and bound-agent controls</li>
            <li>Approving receipts are one-time execution gates with exact payload and spend checks</li>
            <li>Validators fetch two to four independent HTTPS sources and commit snapshot hashes</li>
            <li>Emergency pause and agent rotation paths</li>
          </ul>
        </aside>

        <section className="audit">
          <div className="panel-title"><span>03</span><h2>Evidence pack</h2></div>
          <p>The evidence pack binds the mandate, approving receipt, verified source manifest, action hash, policy hashes, accepted-write sequence, and execution gate into one exportable review object.</p>
          <div className="actions three">
            <button className="secondary" onClick={readTimeline}>Load receipt timeline</button>
            <button onClick={readPack}>Load evidence pack</button>
            <button className="secondary" onClick={copyPack}>Copy pack</button>
          </div>
          <div className="audit-grid">
            <pre>{timeline || "No timeline loaded yet."}</pre>
            <pre>{pack || "No evidence pack loaded yet."}</pre>
          </div>
        </section>
      </section>
    </main>
  );
}
