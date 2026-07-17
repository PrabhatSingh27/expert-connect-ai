import { apiRequest } from "./http";
import type { Issue } from "./issues.service";
import type { LoginPayload, LoginResponse } from "./auth.service";
export type ExpertProfilePayload = { fullName: string; email?: string; password?: string; phone: string; bio: string; skills: string[] | string; serviceArea: string; serviceCity?: string; servicePincodes?: string; experienceYears: number; hourlyRate?: number; governmentId?: string; governmentIdFile?: File; permanentAddress?: string; city?: string; pinCode?: string; profileImage?: File; profileImageId?: string };
export type Expert = Omit<ExpertProfilePayload, "password" | "profileImage" | "governmentIdFile"> & { id: string | number; userId?: string | number; expertId?: string | number; email?: string; rating?: number; completedJobs?: number; isAvailable?: boolean; isVerified?: boolean; isActive?: boolean; status?: "pending" | "approved" | "rejected" | "active"; profileImageUrl?: string; profilePhotoUrl?: string; avatarUrl?: string };
type RawExpert = Expert & Record<string, any>;
function normalizeExpert(raw: RawExpert): Expert {
  return { ...raw, fullName: raw.fullName ?? raw.full_name, governmentId: raw.governmentId ?? raw.government_id, serviceArea: raw.serviceArea ?? raw.service_area, serviceCity: raw.serviceCity ?? raw.service_city, servicePincodes: raw.servicePincodes ?? raw.service_pincodes, permanentAddress: raw.permanentAddress ?? raw.permanent_address, experienceYears: raw.experienceYears ?? raw.experience_years ?? 0, profileImageUrl: raw.profileImageUrl ?? raw.profile_image_url, profilePhotoUrl: raw.profilePhotoUrl ?? raw.profile_photo_url, avatarUrl: raw.avatarUrl ?? raw.avatar_url, isVerified: raw.isVerified ?? raw.is_verified, isActive: raw.isActive ?? raw.is_active, status: raw.status ?? (raw.is_verified || raw.isVerified ? "approved" : "pending") };
}
function expertFormData(payload: Partial<ExpertProfilePayload>) {
  const formData = new FormData();
  const append = (key: string, value: unknown) => { if (value !== undefined && value !== null && value !== "") formData.append(key, Array.isArray(value) ? value.join(", ") : String(value)); };
  append("full_name", payload.fullName); append("email", payload.email); append("password", payload.password); append("phone", payload.phone); append("government_id", payload.governmentId); append("skills", payload.skills); append("service_area", payload.serviceArea); append("service_city", payload.serviceCity ?? payload.city); append("service_pincodes", payload.servicePincodes ?? payload.pinCode); append("bio", payload.bio); append("permanent_address", payload.permanentAddress); append("experience_years", payload.experienceYears);
  if (payload.profileImage) formData.append("profile_image", payload.profileImage);
  if (payload.governmentIdFile) formData.append("government_id_document", payload.governmentIdFile);
  return formData;
}
export async function listExperts(params?: { skill?: string; location?: string; available?: boolean }) { const q = new URLSearchParams(); if (params?.skill) q.set("skill", params.skill); if (params?.location) q.set("location", params.location); if (typeof params?.available === "boolean") q.set("available", String(params.available)); const rows = await apiRequest<RawExpert[]>(`/experts/${q.size ? `?${q}` : ""}`); return rows.map(normalizeExpert); }
export async function getExpertDetails(expertId: string | number) { return normalizeExpert(await apiRequest<RawExpert>(`/experts/${expertId}`)); }
export async function expertSignup(payload: ExpertProfilePayload) { return normalizeExpert(await apiRequest<RawExpert>("/experts/signup", { method: "POST", body: expertFormData(payload), auth: false })); }
export function expertLogin(payload: LoginPayload) { return apiRequest<LoginResponse>("/experts/login", { method: "POST", body: JSON.stringify(payload), auth: false }); }
export function createExpertProfile(payload: ExpertProfilePayload) { return expertSignup(payload); }
export async function getMyExpertProfile() { return normalizeExpert(await apiRequest<RawExpert>("/experts/me")); }
export async function updateExpertProfile(payload: Partial<ExpertProfilePayload>) { return normalizeExpert(await apiRequest<RawExpert>("/experts/profile/me", { method: "PUT", body: expertFormData(payload) })); }
export function listAssignedExpertIssues() { return apiRequest<Issue[]>("/experts/issues"); }
export function getAssignedExpertIssue(issueId: string | number) { return apiRequest<Issue>(`/experts/issues/${issueId}`); }
export function acceptAssignedIssue(issueId: string | number) { return apiRequest<Issue>(`/experts/issues/${issueId}/accept`, { method: "PATCH" }); }
export function rejectAssignedIssue(issueId: string | number) { return apiRequest<Issue>(`/experts/issues/${issueId}/reject`, { method: "PATCH" }); }
export function updateAssignedIssueStatus(issueId: string | number, status: string) { return apiRequest<Issue>(`/experts/issues/${issueId}/status`, { method: "PATCH", body: JSON.stringify({ status }) }); }
export function getCompletedExpertJobs() { return apiRequest<Issue[]>("/expert/jobs/completed"); }
export function getExpertEarnings() { return apiRequest<{ totalEarnings: number; completedJobs: number; currency?: string }>("/expert/earnings"); }
