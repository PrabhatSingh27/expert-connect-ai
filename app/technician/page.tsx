"use client";

import { useEffect, useMemo, useState } from "react";
import { BadgeCheck, Briefcase, CalendarPlus, CheckCircle2, Pencil, RefreshCw, Star, Trash2, UserRound } from "lucide-react";
import { acceptAssignedIssue, createSlot, deleteSlot, formatAverageRating, getAverageRating, getMyAvailabilities, getMyExpertProfile, listAssignedExpertIssues, listExpertReviews, updateExpertProfile, updateIssueDiagnosis, updateIssueStatus, updateSlot, type AvailabilitySlot, type Expert, type Issue, type Review } from "@/services";
import { Card, DashboardShell, EmptyState, LoadingState, StatCard, StatusPill } from "@/components/ui-kit";
import { IssueDetailPanel } from "@/components/issue-detail-panel";
import { AiResultCard } from "@/components/ai-result-card";

const days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const blankSlot = { dayOfWeek: "Monday", startTime: "09:00", endTime: "17:00" };

export default function TechnicianPage() {
  const [profile, setProfile] = useState<Expert | null>(null);
  const [jobs, setJobs] = useState<Issue[]>([]);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [slots, setSlots] = useState<AvailabilitySlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [busyIssueId, setBusyIssueId] = useState("");
  const [slot, setSlot] = useState(blankSlot);
  const [editingSlot, setEditingSlot] = useState<AvailabilitySlot | null>(null);
  const [editProfile, setEditProfile] = useState(false);
  const [profileFile, setProfileFile] = useState<File>();
  const [profileForm, setProfileForm] = useState({ fullName: "", phone: "", serviceArea: "", serviceCity: "", servicePincodes: "", permanentAddress: "", bio: "", experienceYears: "0" });

  async function refresh() {
    setLoading(true);
    const [profileResult, jobsResult, slotsResult] = await Promise.allSettled([getMyExpertProfile(), listAssignedExpertIssues(), getMyAvailabilities()]);
    if (profileResult.status === "fulfilled") {
      setProfile(profileResult.value);
      setProfileForm({ fullName: profileResult.value.fullName || "", phone: profileResult.value.phone || "", serviceArea: profileResult.value.serviceArea || "", serviceCity: profileResult.value.serviceCity || "", servicePincodes: profileResult.value.servicePincodes || "", permanentAddress: profileResult.value.permanentAddress || "", bio: profileResult.value.bio || "", experienceYears: String(profileResult.value.experienceYears || 0) });
      try { setReviews(await listExpertReviews(profileResult.value.id)); } catch { setReviews([]); }
    }
    if (jobsResult.status === "fulfilled") setJobs(jobsResult.value);
    if (slotsResult.status === "fulfilled") setSlots(slotsResult.value);
    setLoading(false);
  }

  useEffect(() => { refresh(); }, []);
  const activeJobs = useMemo(() => jobs.filter((job) => !["completed", "closed", "rejected"].includes(job.status)), [jobs]);
  const averageRating = getAverageRating(reviews) ?? profile?.rating ?? null;

  async function runIssueAction(issueId: string | number, status: "in_progress" | "completed") {
    setBusyIssueId(String(issueId)); setMessage("");
    try { await updateIssueStatus(issueId, status); setMessage(status === "completed" ? "Issue marked complete." : "Work started."); await refresh(); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Issue action failed"); }
    finally { setBusyIssueId(""); }
  }

  async function saveSlot(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); setMessage("");
    try { await createSlot(slot); setSlot(blankSlot); setMessage("Availability slot created."); await refresh(); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Availability create failed"); }
  }
  async function saveSlotEdit() {
    if (!editingSlot) return;
    try { await updateSlot(editingSlot.id, editingSlot); setEditingSlot(null); setMessage("Availability slot updated."); await refresh(); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Availability update failed"); }
  }
  async function saveProfile(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try { await updateExpertProfile({ ...profileForm, experienceYears: Number(profileForm.experienceYears), profileImage: profileFile }); setEditProfile(false); setProfileFile(undefined); setMessage("Profile updated."); await refresh(); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Profile update failed"); }
  }
  const profilePhoto = (profile as Expert & { profileImageUrl?: string; profilePhotoUrl?: string; avatarUrl?: string } | null)?.profileImageUrl || (profile as Expert & { profilePhotoUrl?: string } | null)?.profilePhotoUrl || (profile as Expert & { avatarUrl?: string } | null)?.avatarUrl;

  return <DashboardShell title="Expert dashboard" subtitle="Manage profile, weekly availability, and assigned jobs." action={<button onClick={refresh} className="inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm font-bold"><RefreshCw size={15}/>Refresh</button>}>
    <div className="grid gap-4 md:grid-cols-4"><StatCard label="Assigned jobs" value={jobs.length} icon={<Briefcase size={20}/>}/><StatCard label="Active jobs" value={activeJobs.length} icon={<BadgeCheck size={20}/>}/><StatCard label="Availability slots" value={slots.length} icon={<CalendarPlus size={20}/>}/><StatCard label="Rating" value={formatAverageRating(averageRating)} icon={<Star size={20}/>}/></div>
    {message && <p className="mt-4 rounded-xl bg-white/70 p-3 text-sm font-bold text-slate-600">{message}</p>}
    {loading ? <div className="mt-6"><LoadingState/></div> : <div className="mt-6 grid gap-6 lg:grid-cols-[.9fr_1.1fr]"><div className="space-y-6">
      <Card className="p-5"><div className="mb-4 flex items-center justify-between gap-3"><div className="flex items-center gap-3">{profilePhoto ? <img src={profilePhoto} alt="Profile" className="h-11 w-11 rounded-full object-cover"/> : <span className="grid h-11 w-11 place-items-center rounded-full bg-teal-100 font-black text-teal-800">{profile?.fullName?.slice(0,1) || <UserRound size={18}/>}</span>}<h2 className="font-black">Expert profile</h2></div><button onClick={() => setEditProfile(!editProfile)} className="rounded-lg border p-2" aria-label="Edit profile"><Pencil size={16}/></button></div>
      {editProfile ? <form onSubmit={saveProfile} className="grid gap-3"><input className="input" placeholder="Full name" value={profileForm.fullName} onChange={e=>setProfileForm({...profileForm,fullName:e.target.value})} required/><input className="input" placeholder="Phone" value={profileForm.phone} onChange={e=>setProfileForm({...profileForm,phone:e.target.value})} required/><input className="input" placeholder="Service area" value={profileForm.serviceArea} onChange={e=>setProfileForm({...profileForm,serviceArea:e.target.value})} required/><div className="grid gap-3 sm:grid-cols-2"><input className="input" placeholder="City" value={profileForm.serviceCity} onChange={e=>setProfileForm({...profileForm,serviceCity:e.target.value})}/><input className="input" placeholder="PIN codes" value={profileForm.servicePincodes} onChange={e=>setProfileForm({...profileForm,servicePincodes:e.target.value})}/></div><textarea className="input min-h-20" placeholder="Permanent address" value={profileForm.permanentAddress} onChange={e=>setProfileForm({...profileForm,permanentAddress:e.target.value})}/><textarea className="input min-h-20" placeholder="Bio" value={profileForm.bio} onChange={e=>setProfileForm({...profileForm,bio:e.target.value})}/><input className="input" type="number" min="0" placeholder="Experience years" value={profileForm.experienceYears} onChange={e=>setProfileForm({...profileForm,experienceYears:e.target.value})}/><input className="input" type="file" accept="image/*" onChange={e=>setProfileFile(e.target.files?.[0])}/><button className="rounded-xl bg-slate-950 px-4 py-3 font-bold text-white">Save profile</button></form> : profile ? <div className="space-y-2 text-sm text-slate-600"><p className="font-black text-slate-950">{profile.fullName}</p><p>{profile.phone}</p><p>{profile.serviceArea}</p><p>{profile.bio}</p><StatusPill tone={profile.status === "approved" || profile.status === "active" ? "good" : "warn"}>{profile.status || "pending"}</StatusPill></div> : <EmptyState title="No expert profile" text="Apply from Become Expert page first."/>}</Card>
      <Card className="p-5"><div className="mb-4 flex items-center justify-between gap-3"><h2 className="font-black">My reviews</h2><StatusPill tone="info">Average {formatAverageRating(averageRating)}</StatusPill></div>{reviews.length===0?<p className="text-sm text-slate-500">Customer reviews for your expert profile will appear here.</p>:<div className="space-y-3">{reviews.map(item=><div key={item.id} className="rounded-xl border p-3 text-sm"><p className="font-black text-amber-500">{"★".repeat(item.rating)}</p><p className="text-slate-600">{item.review || item.comment || "No review text"}</p></div>)}</div>}</Card>
      <Card className="p-5"><h2 className="mb-1 font-black">Create availability</h2><p className="mb-4 text-sm text-slate-500">POST /availability/ with day, start time, and end time.</p><form onSubmit={saveSlot} className="grid gap-3"><select className="input" value={slot.dayOfWeek} onChange={e=>setSlot({...slot,dayOfWeek:e.target.value})}>{days.map(day=><option key={day}>{day}</option>)}</select><div className="grid gap-3 sm:grid-cols-2"><input className="input" type="time" value={slot.startTime} onChange={e=>setSlot({...slot,startTime:e.target.value})} required/><input className="input" type="time" value={slot.endTime} onChange={e=>setSlot({...slot,endTime:e.target.value})} required/></div><button className="rounded-xl bg-slate-950 px-5 py-3 font-bold text-white">Add slot</button></form></Card>
      <Card className="p-5"><h2 className="mb-4 font-black">My availability</h2>{slots.length===0?<p className="text-sm text-slate-500">No weekly slots yet.</p>:<div className="space-y-3">{slots.map(item=><div key={item.id} className="rounded-xl border p-3 text-sm"><div className="flex items-center justify-between gap-2"><span className="font-bold">{item.dayOfWeek}: {item.startTime} - {item.endTime}</span><div className="flex gap-2"><button onClick={()=>setEditingSlot({...item})} className="rounded-lg border p-2" aria-label="Edit slot"><Pencil size={14}/></button><button onClick={async()=>{try{await deleteSlot(item.id);setMessage("Availability slot removed.");refresh();}catch(error){setMessage(error instanceof Error?error.message:"Availability removal failed")}}} className="rounded-lg border border-rose-200 p-2 text-rose-600" aria-label="Remove slot"><Trash2 size={14}/></button></div></div>{editingSlot?.id===item.id&&<div className="mt-3 grid gap-2"><select className="input" value={editingSlot.dayOfWeek} onChange={e=>setEditingSlot({...editingSlot,dayOfWeek:e.target.value})}>{days.map(day=><option key={day}>{day}</option>)}</select><div className="grid gap-2 sm:grid-cols-2"><input className="input" type="time" value={editingSlot.startTime} onChange={e=>setEditingSlot({...editingSlot,startTime:e.target.value})}/><input className="input" type="time" value={editingSlot.endTime} onChange={e=>setEditingSlot({...editingSlot,endTime:e.target.value})}/></div><button onClick={saveSlotEdit} className="rounded-lg bg-slate-950 px-3 py-2 text-sm font-bold text-white">Save slot</button></div>}</div>)}</div>}</Card>
    </div><div className="space-y-4">{jobs.length===0?<EmptyState title="No assigned jobs" text="Assigned jobs will appear here."/>:jobs.map(job=><Card key={job.id} className="p-5"><div className="flex flex-col justify-between gap-3 sm:flex-row"><div><h3 className="font-black">{job.title}</h3><p className="mt-1 text-sm text-slate-500">{job.description}</p><p className="mt-2 text-xs text-slate-500">{job.address}</p></div><StatusPill tone="info">{job.status.replaceAll("_"," ")}</StatusPill></div><div className="mt-4"><AiResultCard result={job.aiResult} editable onSave={async(payload)=>{await updateIssueDiagnosis(job.id,payload);await refresh();}}/></div><IssueDetailPanel issue={job} role="expert" onChanged={refresh}/><div className="mt-4 flex flex-wrap gap-2">{job.status==="assigned"&&<button disabled={busyIssueId===String(job.id)} onClick={async()=>{setBusyIssueId(String(job.id));try{await acceptAssignedIssue(job.id);setMessage("Assigned issue accepted.");await refresh();}catch(error){setMessage(error instanceof Error?error.message:"Accept failed");}finally{setBusyIssueId("")}}} className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-bold text-white disabled:opacity-60"><CheckCircle2 size={15} className="mr-2 inline"/>Accept Assigned Issue</button>}<button disabled={busyIssueId===String(job.id)} onClick={()=>runIssueAction(job.id,"in_progress")} className="rounded-xl border px-4 py-2 text-sm font-bold disabled:opacity-60">Start Work</button><button disabled={busyIssueId===String(job.id)} onClick={()=>runIssueAction(job.id,"completed")} className="rounded-xl bg-slate-950 px-4 py-2 text-sm font-bold text-white disabled:opacity-60">Mark Complete</button></div></Card>)}</div></div>}
  </DashboardShell>;
}
