import type { AdminUser } from "@/services";
import { Card, StatusPill } from "@/components/ui-kit";
export function UserTable({ users }: { users: AdminUser[] }) { return <div className="space-y-3">{users.map((user) => <Card key={user.id} className="p-4"><div className="flex justify-between gap-3"><div><h3 className="font-black">{user.name}</h3><p className="mt-1 text-sm text-slate-500">{user.email} · {user.role}</p></div><StatusPill tone={user.status === "active" ? "good" : "danger"}>{user.status}</StatusPill></div></Card>)}</div>; }
