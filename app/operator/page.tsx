"use client";

import { useEffect, useMemo, useState } from "react";
import { ClipboardList, Mail, MapPin, Phone, RefreshCw, UserCheck, Users } from "lucide-react";
import { addIssueNote, assignIssueAsOperator, listExperts, listOperatorIssues, updateIssuePriority, updateIssueStatus, type Expert, type Issue, type IssuePriority, type IssueStatus } from "@/services";
import { Card, DashboardShell, EmptyState, LoadingState, StatCard, StatusPill } from "@/components/ui-kit";
import { IssueDetailPanel } from "@/components/issue-detail-panel";

const statuses: IssueStatus[] = ["operator_review", "need_more_info", "assigned", "in_progress", "completed", "closed", "rejected"];
const priorities: IssuePriority[] = ["low", "medium", "high", "critical"];

function expertPhoto(expert: Expert) {
  return expert.profileImageUrl || expert.profilePhotoUrl || expert.avatarUrl || "";
}

function expertSkills(expert: Expert) {
  return Array.isArray(expert.skills) ? expert.skills.join(", ") : expert.skills || "General service";
}

export default function OperatorPage() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [experts, setExperts] = useState<Expert[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [note, setNote] = useState<Record<string, string>>({});
  const [message, setMessage] = useState("");

  async function refresh() {
    setLoading(true);
    try {
      const [issueResult, expertResult] = await Promise.allSettled([listOperatorIssues(), listExperts({ available: true })]);
      if (issueResult.status === "fulfilled") setIssues(issueResult.value);
      if (expertResult.status === "fulfilled") setExperts(expertResult.value);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { refresh(); }, []);

  async function action(work: Promise<unknown>, ok: string) {
    try {
      await work;
      setMessage(ok);
      await refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Action failed");
    }
  }

  const filtered = useMemo(() => issues.filter((issue) => [issue.title, issue.description, issue.status, issue.category].join(" ").toLowerCase().includes(search.toLowerCase())), [issues, search]);

  return (
    <DashboardShell title="Operator dashboard" subtitle="Manage issue review, priority, notes, and expert assignment." action={<button onClick={refresh} className="inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm font-bold"><RefreshCw size={15} />Refresh</button>}>
      <div className="grid gap-4 md:grid-cols-3">
        <StatCard label="Queue" value={issues.length} icon={<ClipboardList size={20} />} />
        <StatCard label="Open" value={issues.filter((issue) => !["completed", "closed", "rejected"].includes(issue.status)).length} icon={<UserCheck size={20} />} />
        <StatCard label="Available experts" value={experts.length} icon={<Users size={20} />} />
      </div>
      {message && <p className="mt-4 rounded-xl bg-white/70 p-3 text-sm font-bold text-slate-600">{message}</p>}

      <Card className="mt-6 p-5">
        <h2 className="mb-4 font-black">Available expert profiles</h2>
        {experts.length === 0 ? <EmptyState title="No experts" text="Available expert profiles will appear here." /> : (
          <div className="grid gap-3 md:grid-cols-2">
            {experts.map((expert) => {
              const photo = expertPhoto(expert);
              return (
                <div key={expert.id} className="flex gap-3 rounded-2xl border bg-white/60 p-3 text-sm">
                  <span className="grid h-14 w-14 shrink-0 place-items-center overflow-hidden rounded-full bg-teal-100 font-bold text-teal-800">
                    {photo ? <img src={photo} alt={expert.fullName} className="h-full w-full object-cover" /> : expert.fullName.slice(0, 1)}
                  </span>
                  <div className="min-w-0">
                    <p className="font-black">{expert.fullName}</p>
                    <p className="text-slate-600">{expertSkills(expert)}</p>
                    <div className="mt-2 flex flex-wrap gap-2 text-xs font-bold text-slate-500">
                      {expert.phone && <span className="inline-flex items-center gap-1"><Phone size={12} />{expert.phone}</span>}
                      {expert.email && <span className="inline-flex items-center gap-1"><Mail size={12} />{expert.email}</span>}
                      {expert.serviceArea && <span className="inline-flex items-center gap-1"><MapPin size={12} />{expert.serviceArea}</span>}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Card>

      <input className="input mt-6" placeholder="Search queue" value={search} onChange={(event) => setSearch(event.target.value)} />
      <div className="mt-6 space-y-4">
        {loading ? <LoadingState /> : filtered.length === 0 ? <EmptyState title="No issues in queue" text="No operator issues were returned by the backend." /> : filtered.map((issue) => (
          <Card key={issue.id} className="p-5">
            <div className="flex flex-col justify-between gap-3 md:flex-row">
              <div><h3 className="text-lg font-black">{issue.title}</h3><p className="mt-1 text-sm text-slate-500">{issue.description}</p><p className="mt-2 text-xs text-slate-500">{issue.location} {issue.pinCode}</p></div>
              <StatusPill tone="info">{issue.status.replaceAll("_", " ")}</StatusPill>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <select className="input" value={issue.status} onChange={(event) => action(updateIssueStatus(issue.id, event.target.value as IssueStatus), "Status updated")}>{statuses.map((status) => <option key={status} value={status}>{status}</option>)}</select>
              <select className="input" value={issue.priority || "medium"} onChange={(event) => action(updateIssuePriority(issue.id, event.target.value as IssuePriority), "Priority updated")}>{priorities.map((priority) => <option key={priority} value={priority}>{priority}</option>)}</select>
              <select className="input" defaultValue="" onChange={(event) => event.target.value && action(assignIssueAsOperator(issue.id, event.target.value), "Expert assigned")}><option value="">Assign expert</option>{experts.map((expert) => <option key={expert.id} value={expert.id}>{expert.fullName}</option>)}</select>
            </div>
            <IssueDetailPanel issue={issue} role="operator" onChanged={refresh} />
            <div className="mt-3 flex gap-2">
              <input className="input" placeholder="Operator note" value={note[issue.id] || ""} onChange={(event) => setNote({ ...note, [issue.id]: event.target.value })} />
              <button onClick={() => note[issue.id]?.trim() && action(addIssueNote(issue.id, note[issue.id]), "Note saved")} className="rounded-xl bg-slate-950 px-4 py-2 text-sm font-bold text-white">Save</button>
            </div>
          </Card>
        ))}
      </div>
    </DashboardShell>
  );
}
