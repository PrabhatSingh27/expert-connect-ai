import { NextResponse } from "next/server";
export async function POST(request: Request) { const body = await request.json(); const res = await fetch("http://172.17.38.216:8000/auth/register", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }); const data = await res.json().catch(() => ({})); return NextResponse.json(data, { status: res.status }); }
