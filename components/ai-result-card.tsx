"use client";

import { useEffect, useState } from "react";
import { Brain, Clock, Gauge, UserRound } from "lucide-react";
import { Card, StatusPill } from "./ui-kit";
import type { AiResult } from "@/services";

type Props = {
  result?: AiResult;
  editable?: boolean;
  onSave?: (payload: { detectedProblem: string; response: string }) => Promise<void> | void;
};

export function AiResultCard({ result, editable = false, onSave }: Props) {
  const expertName = result?.assignedExpert || result?.expert?.fullName || result?.expert?.name;
  const response = result?.estimatedResponseTime || result?.responseMessage || result?.response || result?.responseStatus;
  const [detectedProblem, setDetectedProblem] = useState(result?.detectedProblem || "");
  const [expertResponse, setExpertResponse] = useState(response || "");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    setDetectedProblem(result?.detectedProblem || "");
    setExpertResponse(response || "");
  }, [result?.detectedProblem, response]);

  if (!result) return null;

  async function save(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!onSave) return;
    setSaving(true);
    setMessage("");
    try {
      await onSave({ detectedProblem: detectedProblem.trim(), response: expertResponse.trim() });
      setMessage("AI classification updated.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Update failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card className="p-5">
      <div className="mb-5 flex items-center gap-3">
        <div className="grid h-11 w-11 place-items-center rounded-2xl bg-linear-to-br from-teal-200 via-sky-200 to-violet-200 text-slate-950"><Brain size={20} /></div>
        <div><h3 className="font-black">AI classification</h3><p className="text-sm text-slate-500 dark:text-slate-400">LLM/NLP response from backend</p></div>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <Info icon={<Gauge size={18} />} label="Detected" value={detectedProblem || "Pending"} />
        <Info icon={<Brain size={18} />} label="Category" value={result.category || "Pending"} />
        <Info icon={<Clock size={18} />} label="Response" value={expertResponse || "Pending"} />
        <Info icon={<UserRound size={18} />} label="Expert" value={expertName || "Pending"} />
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {result.urgency && <StatusPill tone="warn">Urgency: {result.urgency}</StatusPill>}
        {result.priority && <StatusPill tone="danger">Priority: {result.priority}</StatusPill>}
        {typeof result.confidence === "number" && <StatusPill tone="info">Confidence: {Math.round(result.confidence)}%</StatusPill>}
      </div>
      {editable && (
        <form onSubmit={save} className="mt-4 grid gap-3">
          <input className="input" placeholder="Update detected problem" value={detectedProblem} onChange={(event) => setDetectedProblem(event.target.value)} />
          <textarea className="input min-h-24" placeholder="Update response" value={expertResponse} onChange={(event) => setExpertResponse(event.target.value)} />
          <button disabled={saving} className="rounded-xl bg-slate-950 px-4 py-3 text-sm font-bold text-white disabled:opacity-60">{saving ? "Saving..." : "Save detected & response"}</button>
          {message && <p className="text-sm font-bold text-slate-600">{message}</p>}
        </form>
      )}
    </Card>
  );
}

function Info({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return <div className="rounded-2xl border border-slate-200/70 bg-white/48 p-4 backdrop-blur dark:border-white/10 dark:bg-white/[.04]"><div className="mb-2 flex items-center gap-2 text-slate-500 dark:text-slate-400">{icon}<span className="text-xs font-bold uppercase">{label}</span></div><p className="font-black">{value}</p></div>;
}
