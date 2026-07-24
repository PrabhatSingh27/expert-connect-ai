"use client";

import { useEffect, useMemo, useState } from "react";
import { Brain, CalendarDays, Camera, CheckCircle2, Clock, FileText, Mail, MapPin, Phone, PlusCircle, Star, Upload, UserRound } from "lucide-react";
import { AiResultCard } from "@/components/ai-result-card";
import { IssueDetailPanel } from "@/components/issue-detail-panel";
import { MediaUploadManager, type MediaUploadValue } from "@/components/media-upload-manager";
import { ToastStack } from "@/components/toast-stack";
import { useToast } from "@/hooks/use-toast";
import { Card, DashboardShell, EmptyState, LoadingState, StatCard, StatusPill } from "@/components/ui-kit";
import { autoAssignIssueRoundRobin, createIssue, deleteIssue, getMe, listExperts, listIssues, updateMe, type AiResult, type AuthUser, type Expert, type Issue } from "@/services";

const emptyForm = { title: "", description: "", preferredVisitDate: "", preferredTime: "", location: "", address: "", pinCode: "" };
const emptyMedia: MediaUploadValue = { imageIds: [], mediaIds: [], files: [], isUploading: false, hasErrors: false };
const phases = ["Uploading...", "Analyzing with AI...", "Detecting Problem...", "Finding Category...", "Setting Priority...", "Assigning Expert..."];

function expertPhoto(expert: Expert) {
  return expert.profileImageUrl || expert.profilePhotoUrl || expert.avatarUrl;
}

function expertSkills(expert: Expert) {
  return Array.isArray(expert.skills) ? expert.skills.join(", ") : expert.skills || "General service";
}

export default function CustomerPage() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [experts, setExperts] = useState<Expert[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [media, setMedia] = useState(emptyMedia);
  const [aiPreview, setAiPreview] = useState<AiResult>();
  const [profile, setProfile] = useState<AuthUser>();
  const [profileEdit, setProfileEdit] = useState(false);
  const [profileForm, setProfileForm] = useState({ name: "", email: "", phone: "" });
  const [profileFile, setProfileFile] = useState<File>();
  const [profilePreview, setProfilePreview] = useState("");
  const [phase, setPhase] = useState(-1);
  const { toasts, toast, closeToast } = useToast();

  async function refresh() {
    setLoading(true);
    try {
      const [issuesResult, profileResult, expertsResult] = await Promise.allSettled([listIssues({ mine: true }), getMe(), listExperts()]);
      setIssues(issuesResult.status === "fulfilled" ? issuesResult.value : []);
      if (profileResult.status === "fulfilled") {
        setProfile(profileResult.value);
        setProfileForm({
          name: profileResult.value.name || "",
          email: profileResult.value.email || "",
          phone: profileResult.value.phone || profileResult.value.phone_number || "",
        });
      }
      if (expertsResult.status === "fulfilled") setExperts(expertsResult.value);
    } catch {
      setIssues([]);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { refresh(); }, []);

  const active = useMemo(() => issues.filter((issue) => !["closed", "completed", "rejected"].includes(issue.status)).length, [issues]);
  const profilePhoto = profilePreview || profile?.profileImageUrl || profile?.profile_image_url || profile?.avatarUrl;

  function chooseProfileImage(file?: File) {
    if (!file) return;
    if (!file.type.startsWith("image/")) return toast("Profile picture must be an image.", "error");
    if (file.size > 10 * 1024 * 1024) return toast("Profile picture must be under 10 MB.", "error");
    setProfileFile(file);
    setProfilePreview(URL.createObjectURL(file));
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (media.isUploading) return toast("Media is still uploading.", "info");
    if (media.hasErrors) return toast("Fix failed uploads before submit.", "error");
    setSaving(true);
    let idx = 0;
    setPhase(0);
    const timer = window.setInterval(() => {
      idx = Math.min(phases.length - 1, idx + 1);
      setPhase(idx);
    }, 800);
    try {
      const created = await createIssue({ ...form, mediaIds: media.mediaIds, files: media.files });
      if (created.aiResult) setAiPreview(created.aiResult);
      try {
        const availableExperts = await listExperts({ available: true });
        const assigned = await autoAssignIssueRoundRobin(created.id, availableExperts);
        setAiPreview(assigned.aiResult || created.aiResult);
        toast("Issue submitted and assigned automatically.", "success");
      } catch {
        toast("Issue submitted. Auto assignment will continue from the backend queue.", "info");
      }
      setForm(emptyForm);
      await refresh();
    } catch (error) {
      toast(error instanceof Error ? error.message : "Issue submit failed", "error");
    } finally {
      window.clearInterval(timer);
      setPhase(-1);
      setSaving(false);
    }
  }

  async function saveProfile(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      await updateMe({ ...profileForm, profileImage: profileFile });
      toast("Profile updated.", "success");
      setProfileEdit(false);
      setProfileFile(undefined);
      setProfilePreview("");
      await refresh();
    } catch (error) {
      toast(error instanceof Error ? error.message : "Profile update failed", "error");
    }
  }

  return (
    <DashboardShell title="Customer dashboard" subtitle="Create issues, upload media, run backend AI/NLP classification, and track assignment.">
      <ToastStack toasts={toasts} onClose={closeToast} />
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard label="Total issues" value={issues.length} icon={<FileText size={20} />} />
        <StatCard label="Active" value={active} icon={<Clock size={20} />} />
        <StatCard label="Completed" value={issues.filter((issue) => issue.status === "completed" || issue.status === "closed").length} icon={<CalendarDays size={20} />} />
        <StatCard label="AI ready" value="LLM" icon={<Brain size={20} />} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-[.95fr_1.05fr]">
        <Card className="p-5">
          <div className="mb-5 flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-2xl bg-linear-to-br from-teal-200 via-sky-200 to-violet-200 text-slate-950"><PlusCircle /></div>
            <div><h2 className="font-black">Create new issue</h2><p className="text-sm text-slate-500">Backend AI will classify category and urgency.</p></div>
          </div>
          <form onSubmit={submit} className="space-y-4">
            <input className="input" placeholder="Title" value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} required />
            <textarea className="input min-h-28" placeholder="Description" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} required maxLength={1200} />
            <div className="grid gap-3 sm:grid-cols-2">
              <input className="input" type="date" value={form.preferredVisitDate} onChange={(event) => setForm({ ...form, preferredVisitDate: event.target.value })} />
              <input className="input" type="time" value={form.preferredTime} onChange={(event) => setForm({ ...form, preferredTime: event.target.value })} />
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <input className="input" placeholder="Location" value={form.location} onChange={(event) => setForm({ ...form, location: event.target.value })} required />
              <input className="input" placeholder="PIN code" value={form.pinCode} onChange={(event) => setForm({ ...form, pinCode: event.target.value })} required />
            </div>
            <textarea className="input min-h-20" placeholder="Full address" value={form.address} onChange={(event) => setForm({ ...form, address: event.target.value })} required />
            <MediaUploadManager onChange={setMedia} onToast={toast} />
            {phase >= 0 && <Phase active={phase} />}
            {aiPreview && <AiResultCard result={aiPreview} />}
            <button disabled={saving} className="w-full rounded-2xl bg-slate-950 px-5 py-3 font-black text-white">{saving ? "Submitting..." : "Submit issue"}</button>
          </form>
        </Card>

        <div className="space-y-4">
          <Card className="p-5">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="grid h-14 w-14 place-items-center overflow-hidden rounded-2xl bg-slate-100">
                  {profilePhoto ? <img src={profilePhoto} alt="Customer profile" className="h-full w-full object-cover" /> : <UserRound className="text-slate-400" size={24} />}
                </div>
                <div><h2 className="font-black">My profile</h2><p className="text-sm text-slate-500">Keep your contact details current.</p></div>
              </div>
              <button onClick={() => setProfileEdit(!profileEdit)} className="rounded-lg border px-3 py-2 text-sm font-bold">Edit</button>
            </div>
            {profileEdit ? (
              <form onSubmit={saveProfile} className="grid gap-3">
                <input className="input" value={profileForm.name} onChange={(event) => setProfileForm({ ...profileForm, name: event.target.value })} required />
                <input className="input" type="email" value={profileForm.email} onChange={(event) => setProfileForm({ ...profileForm, email: event.target.value })} required />
                <input className="input" value={profileForm.phone} placeholder="Phone" onChange={(event) => setProfileForm({ ...profileForm, phone: event.target.value })} />
                <label className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-2xl border px-4 py-3 text-sm font-black">
                  <Upload size={16} /> Upload profile picture
                  <input type="file" className="hidden" accept="image/*" onChange={(event) => chooseProfileImage(event.target.files?.[0])} />
                </label>
                <button className="rounded-xl bg-slate-950 px-4 py-3 font-bold text-white">Save profile</button>
              </form>
            ) : (
              <div className="text-sm text-slate-600">
                <p className="font-bold text-slate-950">{profile?.name || "Customer"}</p>
                <p>{profile?.email}</p>
                {(profile?.phone || profile?.phone_number) && <p>{profile.phone || profile.phone_number}</p>}
              </div>
            )}
          </Card>

          <Card className="p-5">
            <div className="mb-4 flex items-center gap-2"><UserRound size={18} /><h2 className="font-black">Available experts</h2></div>
            {experts.length === 0 ? <EmptyState title="No experts found" text="Expert profiles will appear here when available." /> : (
              <div className="grid gap-3">
                {experts.map((expert) => {
                  const photo = expertPhoto(expert);
                  return (
                    <div key={expert.id} className="rounded-2xl border bg-white/60 p-4">
                      <div className="flex gap-4">
                        <div className="grid h-20 w-20 shrink-0 place-items-center overflow-hidden rounded-2xl bg-slate-100">
                          {photo ? <img src={photo} alt={expert.fullName} className="h-full w-full object-cover" /> : <Camera className="text-slate-400" size={26} />}
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <h3 className="font-black">{expert.fullName}</h3>
                            {typeof expert.rating === "number" && <StatusPill tone="info"><Star size={12} className="mr-1 inline" />{expert.rating.toFixed(1)}</StatusPill>}
                          </div>
                          <p className="mt-1 text-sm font-bold text-slate-700">{expertSkills(expert)}</p>
                          <p className="mt-1 text-sm text-slate-500">{expert.bio || "No bio provided."}</p>
                          <div className="mt-3 flex flex-wrap gap-3 text-xs font-bold text-slate-500">
                            {expert.phone && <span className="inline-flex items-center gap-1"><Phone size={13} />{expert.phone}</span>}
                            {expert.email && <span className="inline-flex items-center gap-1"><Mail size={13} />{expert.email}</span>}
                            {expert.serviceArea && <span className="inline-flex items-center gap-1"><MapPin size={13} />{expert.serviceArea}</span>}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Card>

          {loading ? <LoadingState label="Loading issues" /> : issues.length === 0 ? <EmptyState title="No issues yet" text="Your submitted issues will appear here." /> : issues.map((issue) => (
            <Card key={issue.id} className="p-5">
              <div className="flex flex-col justify-between gap-3 sm:flex-row">
                <div><h3 className="text-lg font-black">{issue.title}</h3><p className="mt-1 text-sm text-slate-500">{issue.description}</p></div>
                <StatusPill tone={issue.status === "rejected" ? "danger" : issue.status === "completed" || issue.status === "closed" ? "good" : "info"}>{issue.status.replaceAll("_", " ")}</StatusPill>
              </div>
              <div className="mt-4 flex flex-wrap gap-3 text-sm text-slate-500"><span className="inline-flex items-center gap-1"><MapPin size={15} />{issue.location || issue.pinCode}</span></div>
              <div className="mt-4"><AiResultCard result={issue.aiResult} /></div>
              <IssueDetailPanel issue={issue} role="customer" onChanged={refresh} />
              {issue.status === "submitted" && <button onClick={async () => { await deleteIssue(issue.id); refresh(); }} className="mt-4 rounded-xl border border-rose-200 px-4 py-2 text-sm font-bold text-rose-600">Delete issue</button>}
            </Card>
          ))}
        </div>
      </div>
    </DashboardShell>
  );
}

function Phase({ active }: { active: number }) {
  return (
    <div className="rounded-[1.25rem] border border-teal-400/20 bg-teal-400/10 p-4">
      {phases.map((phase, index) => (
        <div key={phase} className="flex items-center gap-3 py-1 text-sm">
          <span className={`grid h-6 w-6 place-items-center rounded-full text-xs font-black ${index < active ? "bg-emerald-500 text-white" : index === active ? "bg-teal-500 text-white animate-pulse" : "bg-white/60 text-slate-500"}`}>{index < active ? <CheckCircle2 size={14} /> : index + 1}</span>
          <span className={index === active ? "font-black text-teal-800" : "text-slate-500"}>{phase}</span>
        </div>
      ))}
    </div>
  );
}
