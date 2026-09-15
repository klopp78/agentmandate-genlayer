import { createClient } from "genlayer-js";
import { studioDevnet } from "genlayer-js/chains";
import { TransactionStatus } from "genlayer-js/types";

export const AGENT_MANDATE_ADDRESS = "0x9177514caB55a30E2D43deF68C94a1D4a6A22b7b" as const;
export const AGENT_MANDATE_EXPLORER = `https://explorer-studio-dev.genlayer.com/address/${AGENT_MANDATE_ADDRESS}` as const;
export type WalletAddress = `0x${string}`;

function client(account?: WalletAddress) {
  return createClient({ chain: studioDevnet, account });
}

function read(functionName: string, args: string[], account?: WalletAddress) {
  return client(account).readContract({ address: AGENT_MANDATE_ADDRESS, functionName, args, jsonSafeReturn: true });
}

export const readMandate = (id: string, account?: WalletAddress) => read("get_mandate", [id], account);
export const readReceipt = (id: string, account?: WalletAddress) => read("get_receipt", [id], account);
export const readEvidencePack = (id: string, account?: WalletAddress) => read("get_evidence_pack", [id], account);
export const readMandateReceipts = (id: string, account?: WalletAddress) => read("get_mandate_receipts", [id], account);
export const readExecution = (id: string, account?: WalletAddress) => read("get_execution", [id], account);
export const readReceiptExecution = (id: string, account?: WalletAddress) => read("get_receipt_execution", [id], account);
export const readLatestMandateId = (account?: WalletAddress) => read("get_latest_mandate_id", [], account);
export const readLatestReceiptId = (account?: WalletAddress) => read("get_latest_receipt_id", [], account);
export const readLatestExecutionId = (account?: WalletAddress) => read("get_latest_execution_id", [], account);

export async function writeAgentMandate(account: WalletAddress, functionName: string, args: string[]) {
  const sdk = client(account);
  await sdk.connect("studioDevnet");
  const hash = await sdk.writeContract({ address: AGENT_MANDATE_ADDRESS, functionName, args, value: BigInt(0), leaderOnly: false });
  const receipt = await sdk.waitForTransactionReceipt({ hash, status: TransactionStatus.ACCEPTED });
  return { hash, receipt };
}
