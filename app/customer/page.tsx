"use client";
import { useEffect, useMemo, useState } from "react";
import { Brain, CalendarDays, CheckCircle2, Clock, FileText, MapPin, PlusCircle } from "lucide-react";
import { AiResultCard } from "@/components/ai-result-card";
import { MediaUploadManager, type MediaUploadValue } from "@/components/media-upload-manager";
import { ToastStack } from "@/components/toast-stack";
import { useToast } from "@/hooks/use-toast";
import { Card, DashboardShell, EmptyState, LoadingState, StatCard, StatusPill } from "@/components/ui-kit";
import { createIssue, deleteIssue, getMe, listIssues, updateMe, type AiResult, type AuthUser, type Issue } from "@/services";
const emptyForm = { title:"", description:"", preferredVisitDate:"", preferredTime:"", location:"", address:"", pinCode:"" };
const emptyMedia: MediaUploadValue = { imageIds: [], mediaIds: [], files: [], isUploading: false, hasErrors: false };
const phases = ["Uploading...", "Analyzing with AI...", "Detecting Problem...", "Finding Category...", "Setting Priority...", "Assigning Expert..."];
export default function CustomerPage(){
    const [issues,setIssues]=useState<Issue[]>([]); 
    const [loading,setLoading]=useState(true); 
    const [saving,setSaving]=useState(false); 
    const [form,setForm]=useState(emptyForm); 
    const [media,setMedia]=useState(emptyMedia); 
    const [aiPreview,setAiPreview]=useState<AiResult>(); 
    const [profile,setProfile]=useState<AuthUser>();
    const [profileEdit,setProfileEdit]=useState(false);
    const [profileForm,setProfileForm]=useState({name:"",email:"",phone:""});
    const [phase,setPhase]=useState(-1); 
    const {toasts,toast,closeToast}=useToast(); 
    async function refresh(){setLoading(true); 
        try{const [issuesResult,profileResult]=await Promise.allSettled([listIssues({mine:true}),getMe()]); if(issuesResult.status==="fulfilled")setIssues(issuesResult.value); else setIssues([]); if(profileResult.status==="fulfilled"){setProfile(profileResult.value);setProfileForm({name:profileResult.value.name||"",email:profileResult.value.email||"",phone:profileResult.value.phone||profileResult.value.phone_number||""});}
    }catch{setIssues([]);}finally{setLoading(false);

    }} useEffect(()=>{refresh();

    },[]); const active=useMemo(()=>issues.filter(i=>!["closed","completed","rejected"].includes(i.status)).length,[issues]); 
            async function submit(e:React.FormEvent<HTMLFormElement>){e.preventDefault(); 
                if(media.isUploading) 
                    return toast("Media is still uploading.","info"); 
                if(media.hasErrors) 
                    return toast("Fix failed uploads before submit.","error"); 
                setSaving(true); 
                let idx=0; setPhase(0); 
                const timer=window.setInterval(()=>{idx=Math.min(phases.length-1,idx+1); 
                    setPhase(idx);},800); 
                    try{ 
                        const created=await createIssue({...form,mediaIds:media.mediaIds,files:media.files}); 
                        if(created.aiResult) setAiPreview(created.aiResult); 
                        setForm(emptyForm); 
                        toast("Issue submitted successfully.","success"); 
                        await refresh(); 
                    }catch(err)
                    { toast(err instanceof Error?err.message:"Issue submit failed","error"); 

                    }finally{window.clearInterval(timer); 
                        setPhase(-1); setSaving(false);
                    } } return <DashboardShell title="Customer dashboard" subtitle="Create issues, upload media, run backend AI/NLP classification, and track assignment."><ToastStack toasts={toasts} onClose={closeToast}/><div className="grid gap-4 md:grid-cols-4"><StatCard label="Total issues" value={issues.length} icon={<FileText size={20}/>}/><StatCard label="Active" value={active} icon={<Clock size={20}/>}/><StatCard label="Completed" value={issues.filter(i=>i.status==="completed"||i.status==="closed").length} 
                    icon={<CalendarDays size={20}/>}/><StatCard label="AI ready" value="LLM" icon={<Brain size={20}/>}/></div><div className="mt-6 grid gap-6 lg:grid-cols-[.95fr_1.05fr]"><Card className="p-5"><div className="mb-5 flex items-center gap-3"><div className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-teal-200 via-sky-200 to-violet-200 text-slate-950"><PlusCircle/></div><div><h2 className="font-black">Create new issue</h2><p className="text-sm text-slate-500">Backend AI will classify category and urgency.</p></div></div><form onSubmit={submit} className="space-y-4"><input className="input" placeholder="Title" value={form.title} 
                    onChange={e=>setForm({...form,title:e.target.value})} 
                    required/><textarea className="input min-h-28" placeholder="Description" value={form.description} 
                    
                    onChange={e=>setForm({...form,description:e.target.value})} 
                    required maxLength={1200}/><div className="grid gap-3 sm:grid-cols-2"><input className="input" type="date" value={form.preferredVisitDate} 
                    onChange={e=>setForm({...form,preferredVisitDate:e.target.value})}/><input className="input" type="time" value={form.preferredTime} onChange={e=>setForm({...form,preferredTime:e.target.value})}/></div><div className="grid gap-3 sm:grid-cols-2"><input className="input" placeholder="Location" value={form.location} onChange={e=>setForm({...form,location:e.target.value})} 
                    required/><input className="input" placeholder="PIN code" value={form.pinCode} 
                    onChange={e=>setForm({...form,pinCode:e.target.value})} 
                    required/></div><textarea className="input min-h-20" placeholder="Full address" value={form.address} onChange={e=>setForm({...form,address:e.target.value})} 
                    required/><MediaUploadManager onChange={setMedia} onToast={toast}/>{phase>=0&&<Phase active={phase}/>} 
                    
                    {aiPreview&&<AiResultCard result={aiPreview}/>}<button disabled={saving} className="w-full rounded-2xl bg-slate-950 px-5 py-3 font-black text-white">{saving?"Submitting...":"Submit issue"}</button></form></Card><div className="space-y-4"><Card className="p-5"><div className="mb-3 flex items-center justify-between"><div><h2 className="font-black">My profile</h2><p className="text-sm text-slate-500">Keep your contact details current.</p></div><button onClick={()=>setProfileEdit(!profileEdit)} className="rounded-lg border px-3 py-2 text-sm font-bold">Edit</button></div>{profileEdit?<form onSubmit={async e=>{e.preventDefault();try{await updateMe(profileForm);toast("Profile updated.","success");setProfileEdit(false);refresh();}catch(err){toast(err instanceof Error?err.message:"Profile update failed","error");}}} className="grid gap-3"><input className="input" value={profileForm.name} onChange={e=>setProfileForm({...profileForm,name:e.target.value})} required/><input className="input" type="email" value={profileForm.email} onChange={e=>setProfileForm({...profileForm,email:e.target.value})} required/><input className="input" value={profileForm.phone} placeholder="Phone" onChange={e=>setProfileForm({...profileForm,phone:e.target.value})}/><button className="rounded-xl bg-slate-950 px-4 py-3 font-bold text-white">Save profile</button></form>:<div className="text-sm text-slate-600"><p className="font-bold text-slate-950">{profile?.name||"Customer"}</p><p>{profile?.email}</p>{profile?.phone&&<p>{profile.phone}</p>}</div>}</Card>{loading?<LoadingState label="Loading issues"/>:issues.length===0?<EmptyState title="No issues yet" text="Your submitted issues will appear here."/>:issues.map(issue=><Card key={issue.id} className="p-5"><div className="flex flex-col justify-between gap-3 sm:flex-row"><div><h3 className="text-lg font-black">{issue.title}</h3><p className="mt-1 text-sm text-slate-500">{issue.description}</p></div><StatusPill tone={issue.status==="rejected"?"danger":issue.status==="completed"||issue.status==="closed"?"good":"info"}>{issue.status.replaceAll("_"," ")}</StatusPill></div><div className="mt-4 flex flex-wrap gap-3 text-sm text-slate-500"><span className="inline-flex items-center gap-1"><MapPin size={15}/>{issue.location||issue.pinCode}</span></div><div className="mt-4"><AiResultCard result={issue.aiResult}/></div>{issue.status==="submitted"&&<button onClick={async()=>{await deleteIssue(issue.id); refresh();}} className="mt-4 rounded-xl border border-rose-200 px-4 py-2 text-sm font-bold text-rose-600">Delete issue</button>}</Card>)}</div></div></DashboardShell> }
function Phase({

    active}:{active:number})
    
{return <div className="rounded-[1.25rem] border border-teal-400/20 bg-teal-400/10 p-4">{phases.map((p,i)=><div key={p} className="flex items-center gap-3 py-1 text-sm"><span className={`grid h-6 w-6 place-items-center rounded-full text-xs font-black ${i<active?"bg-emerald-500 text-white":i===active?"bg-teal-500 text-white animate-pulse":"bg-white/60 text-slate-500"}`}>{i<active?<CheckCircle2 size={14}/>:i+1}</span><span className={i===active?"font-black text-teal-800":"text-slate-500"}>{p}</span></div>)}</div>}
