"use client";

import { useEffect, useMemo, useState } from "react";
import { Mail, MessageCircle, Paperclip, Phone, Send, Star, UserCheck } from "lucide-react";
import { Card, EmptyState, StatusPill } from "@/components/ui-kit";
import { HttpError, formatAverageRating, getAverageRating, getExpertDetails, getIssue, listExpertReviews, listIssueMessages, sendIssueMessage, submitFeedback, submitReview, type ChatMessage, type Expert, type Issue, type Review } from "@/services";

type Props = {
  issue: Issue;
  role: "customer" | "expert" | "operator" | "admin";
  onChanged?: () => void;
};

function mediaKind(type: string, url: string) {
  const value = `${type} ${url}`.toLowerCase();
  if (value.includes("image")) return "image";
  if (value.includes("video")) return "video";
  if (value.includes("audio")) return "audio";
  return "file";
}

export function IssueDetailPanel({ issue, role, onChanged }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [detail, setDetail] = useState<Issue>(issue);
  const [expert, setExpert] = useState<Expert | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [chatText, setChatText] = useState("");
  const [rating, setRating] = useState(5);
  const [review, setReview] = useState("");
  const [message, setMessage] = useState("");
  const [chatBlocked, setChatBlocked] = useState(false);
  const [detailBlocked, setDetailBlocked] = useState(false);

  const assignedExpertId = detail.assignedExpertId || detail.assignedExpert?.id || detail.expert?.id;
  const expertInfo = useMemo(() => ({
    id: assignedExpertId,
    fullName: expert?.fullName || detail.assignedExpert?.fullName || detail.assignedExpert?.name || detail.expert?.fullName || detail.assignedExpertName,
    email: expert?.email || detail.assignedExpert?.email || detail.expert?.email,
    phone: expert?.phone || detail.assignedExpert?.phone || detail.expert?.phone,
    serviceArea: expert?.serviceArea || detail.assignedExpert?.serviceArea || detail.expert?.serviceArea,
    skills: expert?.skills || detail.assignedExpert?.skills || detail.expert?.skills,
  }), [assignedExpertId, detail, expert]);
  const averageRating = getAverageRating(reviews) ?? expert?.rating ?? detail.assignedExpert?.rating ?? detail.expert?.rating ?? null;

  async function load() {
    try {
      const fresh = await getIssue(issue.id);
      setDetail(fresh);
      setDetailBlocked(false);
      const expertId = fresh.assignedExpertId || fresh.assignedExpert?.id || fresh.expert?.id;
      if (expertId) {
        const [expertResult, reviewResult] = await Promise.allSettled([getExpertDetails(expertId), listExpertReviews(expertId)]);
        if (expertResult.status === "fulfilled") setExpert(expertResult.value);
        if (reviewResult.status === "fulfilled") setReviews(reviewResult.value);
      }
      return await loadMessages();
    } catch (error) {
      if (error instanceof HttpError && error.status === 403) {
        setDetailBlocked(true);
        setChatBlocked(true);
        setMessage("You do not have permission to view live details for this issue.");
        return false;
      }
      setMessage(error instanceof Error ? error.message : "Issue details failed");
      return true;
    }
  }

  async function loadMessages() {
    try {
      setMessages(await listIssueMessages(issue.id));
      setChatBlocked(false);
      return true;
    } catch (error) {
      if (error instanceof HttpError && error.status === 403) {
        setChatBlocked(true);
        setMessages([]);
        setMessage("Chat is not available for this issue with the current account.");
        return false;
      }
      setMessages([]);
      return true;
    }
  }

  useEffect(() => {
    if (!expanded) return;
    let stopped = false;
    load().then((ok) => {
      if (!ok) stopped = true;
    });
    const timer = window.setInterval(() => {
      if (!stopped) {
        loadMessages().then((ok) => {
          if (!ok) stopped = true;
        });
      }
    }, 3000);
    return () => window.clearInterval(timer);
  }, [expanded, issue.id]);

  async function sendChat(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!chatText.trim()) return;
    try {
      await sendIssueMessage(issue.id, chatText.trim());
      setChatText("");
      await loadMessages();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Message send failed");
    }
  }

  async function saveReview(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try {
      try { await submitReview(issue.id, { rating, review }); }
      catch { await submitFeedback(issue.id, { rating, review }); }
      setMessage("Review submitted.");
      setReview("");
      await load();
      onChanged?.();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Review submit failed");
    }
  }

  return (
    <div className="mt-4">
      <button onClick={() => setExpanded(!expanded)} className="rounded-xl border px-4 py-2 text-sm font-bold">
        {expanded ? "Hide details" : "View details, media, review & chat"}
      </button>
      {expanded && (
        <div className="mt-4 grid gap-4">
          {message && <p className="rounded-xl bg-white/70 p-3 text-sm font-bold text-slate-600">{message}</p>}

          {!detailBlocked && <Card className="p-5">
            <div className="mb-3 flex items-center gap-2">
              <UserCheck size={18} />
              <h3 className="font-black">Assigned Expert Details</h3>
            </div>
            {expertInfo.id || expertInfo.fullName ? (
              <div className="grid gap-2 text-sm text-slate-600 sm:grid-cols-2">
                <p><b className="text-slate-950">Name:</b> {expertInfo.fullName || "Not available"}</p>
                <p><b className="text-slate-950">Area:</b> {expertInfo.serviceArea || "Not available"}</p>
                <p className="inline-flex items-center gap-2"><Phone size={14} />{expertInfo.phone || "Phone not available"}</p>
                <p className="inline-flex items-center gap-2"><Mail size={14} />{expertInfo.email || "Email not available"}</p>
                <p><b className="text-slate-950">Rating:</b> {formatAverageRating(averageRating)}</p>
                <p className="sm:col-span-2"><b className="text-slate-950">Skills:</b> {Array.isArray(expertInfo.skills) ? expertInfo.skills.join(", ") : expertInfo.skills || "Not listed"}</p>
              </div>
            ) : <EmptyState title="Expert not assigned yet" text="The assigned expert's name, phone, email, and service area will appear here." />}
          </Card>}

          {!detailBlocked && <Card className="p-5">
            <div className="mb-3 flex items-center gap-2">
              <Paperclip size={18} />
              <h3 className="font-black">Uploaded Image / Video / Audio</h3>
            </div>
            {detail.attachments?.length ? (
              <div className="grid gap-3 md:grid-cols-2">
                {detail.attachments.map((item, index) => {
                  const kind = mediaKind(item.fileType, item.fileUrl);
                  return (
                    <div key={`${item.fileUrl}-${index}`} className="rounded-2xl border bg-white/60 p-3">
                      <div className="mb-2 flex items-center justify-between gap-2">
                        <span className="text-sm font-black">{item.fileName || `${kind} file`}</span>
                        <StatusPill tone="info">{kind}</StatusPill>
                      </div>
                      {kind === "image" ? <img src={item.fileUrl} alt={item.fileName || "Issue upload"} className="max-h-56 w-full rounded-xl object-cover" /> : null}
                      {kind === "video" ? <video src={item.fileUrl} controls className="max-h-56 w-full rounded-xl" /> : null}
                      {kind === "audio" ? <audio src={item.fileUrl} controls className="w-full" /> : null}
                      <a href={item.fileUrl} target="_blank" rel="noreferrer" className="mt-2 inline-block text-sm font-bold text-teal-700">Open file</a>
                    </div>
                  );
                })}
              </div>
            ) : <EmptyState title="No media found" text="Uploaded images, videos, and audio from the issue will appear here when provided by the backend." />}
          </Card>}

          {role === "customer" && (
            <Card className="p-5">
              <div className="mb-3 flex items-center gap-2"><Star size={18}/><h3 className="font-black">Customer Review</h3></div>
              <form onSubmit={saveReview} className="grid gap-3">
                <select className="input" value={rating} onChange={(event) => setRating(Number(event.target.value))}>
                  {[5,4,3,2,1].map((value) => <option key={value} value={value}>{value} star</option>)}
                </select>
                <textarea className="input min-h-20" placeholder="Write a review for the expert's work" value={review} onChange={(event) => setReview(event.target.value)} />
                <button className="rounded-xl bg-slate-950 px-4 py-3 text-sm font-bold text-white">Submit review</button>
              </form>
            </Card>
          )}

          {role !== "customer" && reviews.length > 0 && (
            <Card className="p-5">
              <div className="mb-3 flex items-center justify-between gap-3"><h3 className="font-black">Expert Reviews</h3><StatusPill tone="info">Average {formatAverageRating(averageRating)}</StatusPill></div>
              <div className="space-y-3">
                {reviews.map((item) => <div key={item.id} className="rounded-xl border p-3 text-sm"><p className="font-black text-amber-500">{"★".repeat(item.rating)}</p><p className="text-slate-600">{item.review || "No text"}</p></div>)}
              </div>
            </Card>
          )}

          <Card className="p-5">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2"><MessageCircle size={18}/><h3 className="font-black">Live Issue Chat</h3></div>
              <span className="text-xs font-bold text-teal-700">{chatBlocked ? "Auto-update stopped" : "Auto-updates every 3 seconds"}</span>
            </div>
            <div className="mb-3 max-h-72 space-y-2 overflow-auto rounded-2xl bg-white/50 p-3">
              {chatBlocked ? <p className="text-sm text-slate-500">Chat is not available for this issue with the current account.</p> : messages.length === 0 ? <p className="text-sm text-slate-500">No messages yet. Customer, operator, expert, and admin messages will appear here.</p> : messages.map((item) => (
                <div key={item.id} className="rounded-xl bg-white p-3 text-sm shadow-sm">
                  <div className="mb-1 flex items-center justify-between gap-2 text-xs font-bold text-slate-500">
                    <span>{item.senderType || "user"}</span><span>{item.createdAt ? new Date(item.createdAt).toLocaleString() : ""}</span>
                  </div>
                  <p className="text-slate-700">{item.message}</p>
                </div>
              ))}
            </div>
            <form onSubmit={sendChat} className="flex gap-2">
              <input className="input" disabled={chatBlocked} placeholder={chatBlocked ? "Chat unavailable" : "Type message..."} value={chatText} onChange={(event) => setChatText(event.target.value)} />
              <button disabled={chatBlocked} className="rounded-xl bg-slate-950 px-4 text-white disabled:opacity-50"><Send size={16}/></button>
            </form>
          </Card>
        </div>
      )}
    </div>
  );
}
