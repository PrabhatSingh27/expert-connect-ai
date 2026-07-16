"use client";

import { useEffect, useMemo, useState } from "react";
import {
  BadgeCheck,
  Briefcase,
  CalendarPlus,
  CheckCircle2,
  RefreshCw,
  Star,
  UserRound,
} from "lucide-react";
import {
  acceptAssignedIssue,
  createSlot,
  getMyAvailabilities,
  getMyExpertProfile,
  listAssignedExpertIssues,
  updateIssueStatus,
  type AvailabilitySlot,
  type Expert,
  type Issue,
} from "@/services";
import {
  Card,
  DashboardShell,
  EmptyState,
  LoadingState,
  StatCard,
  StatusPill,
} from "@/components/ui-kit";

export default function TechnicianPage() {
  const [profile, setProfile] = useState<Expert | null>(null);
  const [jobs, setJobs] = useState<Issue[]>([]);
  const [slots, setSlots] = useState<AvailabilitySlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [busyIssueId, setBusyIssueId] = useState("");
  const [slot, setSlot] = useState({
    date: "",
    startTime: "",
    endTime: "",
    isAvailable: true,
  });

  async function refresh() {
    setLoading(true);
    try {
      const [profileResult, jobsResult, slotsResult] = await Promise.allSettled([
        getMyExpertProfile(),
        listAssignedExpertIssues(),
        getMyAvailabilities(),
      ]);

      if (profileResult.status === "fulfilled") setProfile(profileResult.value);
      if (jobsResult.status === "fulfilled") setJobs(jobsResult.value);
      if (slotsResult.status === "fulfilled") setSlots(slotsResult.value);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  const activeJobs = useMemo(
    () => jobs.filter((job) => !["completed", "closed", "rejected"].includes(job.status)),
    [jobs]
  );

  async function runIssueAction(issueId: string | number, work: Promise<unknown>, success: string) {
    setBusyIssueId(String(issueId));
    setMessage("");
    try {
      await work;
      setMessage(success);
      await refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Action failed");
    } finally {
      setBusyIssueId("");
    }
  }

  async function saveSlot(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setMessage("");
    try {
      await createSlot(slot);
      setSlot({ date: "", startTime: "", endTime: "", isAvailable: true });
      setMessage("Availability slot created.");
      await refresh();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Availability create failed");
    }
  }

  return (
    <DashboardShell
      title="Expert dashboard"
      subtitle="Assigned issues are fetched from /experts/issues. Accept uses PATCH /experts/issues/{issue_id}/accept."
      action={
        <button
          onClick={refresh}
          className="inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm font-bold"
        >
          <RefreshCw size={15} />
          Refresh
        </button>
      }
    >
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard label="Assigned jobs" value={jobs.length} icon={<Briefcase size={20} />} />
        <StatCard label="Active jobs" value={activeJobs.length} icon={<BadgeCheck size={20} />} />
        <StatCard label="Availability slots" value={slots.length} icon={<CalendarPlus size={20} />} />
        <StatCard label="Rating" value={profile?.rating ?? "-"} icon={<Star size={20} />} />
      </div>

      {message && (
        <p className="mt-4 rounded-xl bg-white/70 p-3 text-sm font-bold text-slate-600">
          {message}
        </p>
      )}

      {loading ? (
        <div className="mt-6">
          <LoadingState />
        </div>
      ) : (
        <div className="mt-6 grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
          <div className="space-y-6">
            <Card className="p-5">
              <div className="mb-4 flex items-center gap-3">
                <UserRound />
                <h2 className="font-black">Expert profile</h2>
              </div>
              {profile ? (
                <div className="space-y-2 text-sm text-slate-600">
                  <p className="font-black text-slate-950">{profile.fullName}</p>
                  <p>{profile.phone}</p>
                  <p>{profile.serviceArea}</p>
                  <p>{profile.bio}</p>
                  <StatusPill tone={profile.status === "approved" || profile.status === "active" ? "good" : "warn"}>
                    {profile.status || "pending"}
                  </StatusPill>
                </div>
              ) : (
                <EmptyState title="No expert profile" text="Apply from Become Expert page first." />
              )}
            </Card>

            <Card className="p-5">
              <h2 className="mb-4 font-black">Create availability</h2>
              <form onSubmit={saveSlot} className="grid gap-3 sm:grid-cols-2">
                <input
                  className="input"
                  type="date"
                  value={slot.date}
                  onChange={(event) => setSlot({ ...slot, date: event.target.value })}
                  required
                />
                <input
                  className="input"
                  type="time"
                  value={slot.startTime}
                  onChange={(event) => setSlot({ ...slot, startTime: event.target.value })}
                  required
                />
                <input
                  className="input"
                  type="time"
                  value={slot.endTime}
                  onChange={(event) => setSlot({ ...slot, endTime: event.target.value })}
                  required
                />
                <button className="rounded-xl bg-slate-950 px-5 py-3 font-bold text-white">
                  Add slot
                </button>
              </form>
            </Card>
          </div>

          <div className="space-y-4">
            {jobs.length === 0 ? (
              <EmptyState
                title="No assigned jobs"
                text="Backend assigned issues from /experts/issues will appear here."
              />
            ) : (
              jobs.map((job) => (
                <Card key={job.id} className="p-5">
                  <div className="flex flex-col justify-between gap-3 sm:flex-row">
                    <div>
                      <h3 className="font-black">{job.title}</h3>
                      <p className="mt-1 text-sm text-slate-500">{job.description}</p>
                      <p className="mt-2 text-xs text-slate-500">{job.address}</p>
                    </div>
                    <StatusPill tone="info">{job.status.replaceAll("_", " ")}</StatusPill>
                  </div>

                  {job.aiResult && (
                    <div className="mt-3 grid gap-2 rounded-2xl bg-white/55 p-3 text-sm text-slate-600">
                      <p><strong>Detected:</strong> {job.aiResult.detectedProblem || "Pending"}</p>
                      <p><strong>Category:</strong> {job.aiResult.category || job.category || "Pending"}</p>
                      <p><strong>Urgency:</strong> {job.aiResult.urgency || "Pending"}</p>
                    </div>
                  )}

                  <div className="mt-4 flex flex-wrap gap-2">
                    {job.status === "assigned" && (
                      <button
                        disabled={busyIssueId === job.id}
                        onClick={() =>
                          runIssueAction(
                            job.id,
                            acceptAssignedIssue(job.id),
                            "Assigned issue accepted."
                          )
                        }
                        className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2 text-sm font-bold text-white disabled:opacity-60"
                      >
                        <CheckCircle2 size={15} />
                        Accept Assigned Issue
                      </button>
                    )}
                    <button
                      disabled={busyIssueId === job.id}
                      onClick={() =>
                        runIssueAction(
                          job.id,
                          updateIssueStatus(job.id, "in_progress"),
                          "Work started."
                        )
                      }
                      className="rounded-xl border px-4 py-2 text-sm font-bold disabled:opacity-60"
                    >
                      Start Work
                    </button>
                    <button
                      disabled={busyIssueId === job.id}
                      onClick={() =>
                        runIssueAction(
                          job.id,
                          updateIssueStatus(job.id, "completed"),
                          "Issue marked complete."
                        )
                      }
                      className="rounded-xl bg-slate-950 px-4 py-2 text-sm font-bold text-white disabled:opacity-60"
                    >
                      Mark Complete
                    </button>
                  </div>
                </Card>
              ))
            )}
          </div>
        </div>
      )}
    </DashboardShell>
  );
}
