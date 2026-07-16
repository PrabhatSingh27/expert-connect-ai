import type { Issue } from "@/services";
import { Card, StatusPill } from "@/components/ui-kit";
export function IssueTable({ issues }: { issues: Issue[] }) { return <div className="space-y-3">{issues.map((issue) => <Card key={issue.id} className="p-4"><div className="flex flex-col justify-between gap-3 md:flex-row"><div><h3 className="font-black">{issue.title}</h3><p className="mt-1 text-sm text-slate-500">{issue.description}</p></div><StatusPill tone="info">{issue.status.replaceAll("_", " ")}</StatusPill></div></Card>)}</div>; }
