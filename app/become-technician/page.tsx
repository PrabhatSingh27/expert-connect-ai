"use client";
import { useState } from "react"; import Link from "next/link"; import { ArrowLeft, BadgeCheck, Camera, Loader2, MapPin, ShieldCheck, Upload, UserRound }
from "lucide-react";
 import { expertSignup } from "@/services";
  import { Card, PageShell } from "@/components/ui-kit";
const initial = { fullName:"", email:"", phone:"", password:"", governmentId:"", serviceAreaCity:"", pinCode:"", permanentAddress:"", bio:"", experienceYears:"" };
export default function BecomeTechnicianPage(){
     const [form,setForm]=useState(initial); 
     const [pic,setPic]=useState<File|null>(null); const [preview,setPreview]=useState("");
      const [loading,setLoading]=useState(false);
       const [message,setMessage]=useState("");
        const [error,setError]=useState("");
         function update(k:keyof typeof initial,v:string){setForm(c=>({...c,[k]:v}));
        } function choose(file?:File){if(!file)return;
             if(!file.type.startsWith("image/")) return setError("Profile picture must be an image.");
              if(file.size>10*1024*1024) return setError("Profile picture must be under 10 MB.");
               setPic(file);
                setPreview(URL.createObjectURL(file));
                 setError("");
                } function validate(){ if(!form.fullName.trim())return"Full name is required.";
                     if(!form.email.trim())return"Email is required.";
                      if(!form.phone.trim())return"Phone number is required.";
                       if(form.password.length<8)return"Password must be at least 8 characters.";
                        if(!form.governmentId.trim())return"Government issued ID is required.";
                         if(!form.serviceAreaCity.trim())return"Service area city is required.";
                          if(!form.pinCode.trim())return"PIN code is required.";
                           if(!form.permanentAddress.trim())return"Permanent address is required.";
                            if(!form.bio.trim())return"Bio is required.";
                             if(Number.isNaN(Number(form.experienceYears))||Number(form.experienceYears)<0)return"Experience years must be valid.";
                              return"";} async function submit(e:React.FormEvent<HTMLFormElement>){e.preventDefault();
                                 const v=validate();
                                  if(v){setError(v);
                                     return;} setLoading(true);
                                      setError("");
                                       setMessage("");
                                        try{await expertSignup({fullName:form.fullName,email:form.email,password:form.password,phone:form.phone,bio:form.bio,skills:"General repair, Home service",serviceArea:`${form.serviceAreaCity} - ${form.pinCode}`,serviceCity:form.serviceAreaCity,servicePincodes:form.pinCode,experienceYears:Number(form.experienceYears),governmentId:form.governmentId,permanentAddress:form.permanentAddress,profileImage:pic || undefined});
                                         setMessage("Expert application submitted successfully.");
                                          setForm(initial);
                                           setPic(null);
                                            setPreview("");}catch(err){setError(err instanceof Error?err.message:"Submission failed.");

                                            }finally{setLoading(false);

                                            }} return <PageShell><section className="mx-auto max-w-6xl px-4 py-8 sm:px-6"><Link href="/" className="mb-6 inline-flex items-center gap-2 text-sm font-bold text-slate-600"><ArrowLeft size={16}/>Back</Link><div className="grid gap-6 lg:grid-cols-[.85fr_1.15fr]"><Card className="p-6"><div className="grid h-14 w-14 place-items-center rounded-2xl bg-gradient-to-br from-teal-200 via-sky-200 to-violet-200 text-slate-950"><BadgeCheck size={28}/></div><h1 className="mt-6 text-4xl font-black tracking-tight">Become an Expert</h1><p className="mt-4 text-sm leading-6 text-slate-600">Create your expert account and submit your technician profile for verification.</p><div className="mt-6 grid gap-3"><Info icon={<UserRound size={18}/>} text="Create expert account"/><Info icon={<ShieldCheck size={18}/>}
                                             text="Verify government issued ID"/><Info icon={<MapPin size={18}/>}
                                              text="Set service area and PIN code"/></div></Card><Card className="p-6"><form onSubmit={submit}
                                               className="space-y-5"><div><h2 className="text-2xl font-black">Expert Details</h2><p className="mt-1 text-sm text-slate-500">Fill all required information carefully.</p></div><div className="grid gap-4 sm:grid-cols-2"><input className="input" placeholder="Full Name" value={form.fullName}
                                                onChange={e=>update("fullName",e.target.value)}
                                                 required/><input className="input" type="email" placeholder="Email" value={form.email}
                                                  onChange={e=>update("email",e.target.value)}
                                                   required/><input className="input" placeholder="Phone Number" value={form.phone}
                                                    onChange={e=>update("phone",e.target.value)}
                                                     required/><input className="input" type="password" placeholder="Create Password" value={form.password}
                                                      onChange={e=>update("password",e.target.value)}
                                                       required minLength={8}/><input className="input" placeholder="Government Issued ID" value={form.governmentId}
                                                        onChange={e=>update("governmentId",e.target.value)}
                                                         required/><input className="input" type="number" placeholder="Experience Years" value={form.experienceYears}
                                                          onChange={e=>update("experienceYears",e.target.value)}
                                                           required min={0}/><input className="input" placeholder="Service Area City" value={form.serviceAreaCity}
                                                            onChange={e=>update("serviceAreaCity",e.target.value)}
                                                             required/><input className="input" placeholder="PIN Code" value={form.pinCode}
                                                              onChange={e=>update("pinCode",e.target.value)}
                                                               required/></div><textarea className="input min-h-24" placeholder="Permanent Address" value={form.permanentAddress}
                                                                onChange={e=>update("permanentAddress",e.target.value)}
                                                                 required/><textarea className="input min-h-28" placeholder="Bio" value={form.bio}
                                                                  onChange={e=>update("bio",e.target.value)}
                                                                   required maxLength={800}/><div className="rounded-2xl border border-dashed border-slate-300/80 bg-white/45 p-5"><div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"><div className="flex items-center gap-4"><div className="grid h-20 w-20 place-items-center overflow-hidden rounded-2xl bg-slate-100">{preview?<img src={preview} alt="Profile preview" className="h-full w-full object-cover"/>:<Camera className="text-slate-400" size={28}/>}
                                                                   </div><div><p className="font-black">Profile Picture</p><p className="mt-1 text-xs text-slate-500">JPG, PNG, WEBP up to 10 MB</p></div></div><label className="inline-flex cursor-pointer items-center justify-center gap-2 rounded-2xl bg-slate-950 px-4 py-3 text-sm font-black text-white"><Upload size={16}/>Upload<input type="file" className="hidden" accept="image/*" onChange={e=>choose(e.target.files?.[0])}/></label></div></div>{error&&<p className="rounded-xl bg-rose-500/10 px-4 py-3 text-sm font-bold text-rose-700">{error}</p>}
                                                                   {message&&<p className="rounded-xl bg-emerald-500/10 px-4 py-3 text-sm font-bold text-emerald-700">{message}</p>}<button type="submit" disabled={loading}
                                                                    className="flex w-full items-center justify-center gap-2 rounded-2xl bg-slate-950 px-5 py-3 font-black text-white">{loading&&<Loader2 className="animate-spin" size={18}/>} 
                                                                    {loading?"Submitting...":"Submit Expert Application"}
                                                                    </button></form></Card></div></section></PageShell>}
function Info({icon,text}:{icon:React.ReactNode;text:string}

){return <div className="flex items-center gap-3 rounded-2xl border border-slate-200/70 bg-white/50 px-4 py-3 text-sm font-bold"><span className="text-teal-600">{icon}</span>{text}</div>}
