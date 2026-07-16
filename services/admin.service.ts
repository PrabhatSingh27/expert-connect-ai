import { apiRequest } from "./http";
import type { Expert } from "./experts.service";
import type { Issue } from "./issues.service";
export type AdminUser = { id: string | number; name: string; email: string; role: string; status: "active" | "suspended"; isActive?: boolean; createdAt?: string };
export type AdminOverview = { totalUsers: number; totalExperts?: number; totalVerifiedExperts?: number; totalIssues: number; openIssues?: number; activeExperts?: number; issuesByStatus?: Record<string, number>; operators?: number };
type RawAdminOverview = AdminOverview & Record<string, any>;
function normalizeOverview(raw: RawAdminOverview): AdminOverview {
  return { ...raw, totalUsers: raw.totalUsers ?? raw.total_users ?? 0, totalExperts: raw.totalExperts ?? raw.total_experts, totalVerifiedExperts: raw.totalVerifiedExperts ?? raw.total_verified_experts, totalIssues: raw.totalIssues ?? raw.total_issues ?? 0, issuesByStatus: raw.issuesByStatus ?? raw.issues_by_status, activeExperts: raw.activeExperts ?? raw.total_verified_experts ?? raw.totalExperts ?? raw.total_experts, openIssues: raw.openIssues ?? raw.issues_by_status?.open ?? raw.issuesByStatus?.open };
}
function normalizeUser(user: AdminUser & Record<string, any>): AdminUser {
  const isActive = user.isActive ?? user.is_active ?? user.status === "active";
  return { ...user, id: user.id, name: user.name || user.email, isActive, status: isActive ? "active" : "suspended", createdAt: user.createdAt ?? user.created_at };
}
export async function getAdminOverview() { return normalizeOverview(await apiRequest<RawAdminOverview>("/admin/overview")); }
export const getNormalizedAdminOverview = getAdminOverview;
export async function listUsers(params?: { role?: string }) { const q = new URLSearchParams(); if (params?.role) q.set("role", params.role); const rows = await apiRequest<Array<AdminUser & Record<string, any>>>(`/admin/users${q.size ? `?${q}` : ""}`); return rows.map(normalizeUser); }
export async function updateUserStatus(userId: string | number, status: AdminUser["status"]) { return normalizeUser(await apiRequest<AdminUser & Record<string, any>>(`/admin/users/${userId}/status`, { method: "PATCH", body: JSON.stringify({ isActive: status === "active", is_active: status === "active" }) })); }
export function listExpertApplications() { return apiRequest<Expert[]>("/admin/experts/applications"); }
export function approveExpert(expertId: string | number) { return apiRequest<Expert>(`/admin/experts/${expertId}/verify`, { method: "PATCH", body: JSON.stringify({ isVerified: true, is_verified: true }) }); }
export function rejectExpert(expertId: string | number) { return apiRequest<Expert>(`/admin/experts/${expertId}/status`, { method: "PATCH", body: JSON.stringify({ isActive: false, is_active: false }) }); }
export function updateExpertStatus(expertId: string | number, isActive: boolean) { return apiRequest<Expert>(`/admin/experts/${expertId}/status`, { method: "PATCH", body: JSON.stringify({ isActive, is_active: isActive }) }); }
export function verifyExpert(expertId: string | number, isVerified = true) { return apiRequest<Expert>(`/admin/experts/${expertId}/verify`, { method: "PATCH", body: JSON.stringify({ isVerified, is_verified: isVerified }) }); }
export function listAllIssues() { return apiRequest<Issue[]>("/admin/issues"); }
export function listAdminExperts() { return apiRequest<Expert[]>("/admin/experts"); }
export function getAdminAnalytics() { return apiRequest<AdminOverview>("/admin/analytics"); }
