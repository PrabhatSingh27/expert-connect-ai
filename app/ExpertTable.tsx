import type { Expert } from "@/services";
import { Card, StatusPill } from "@/components/ui-kit";
function skillsLabel(skills: Expert["skills"]) { return Array.isArray(skills) ? skills.join(", ") : skills || "No skills"; }
export function ExpertTable({ experts }: { experts: Expert[] }) { return <div className="space-y-3">{experts.map((expert) => <Card key={expert.id} className="p-4"><div className="flex justify-between gap-3"><div><h3 className="font-black">{expert.fullName}</h3><p className="mt-1 text-sm text-slate-500">{skillsLabel(expert.skills)} · {expert.serviceArea}</p></div><StatusPill tone={expert.status === "approved" ? "good" : "warn"}>{expert.status || "pending"}</StatusPill></div></Card>)}</div>; }
