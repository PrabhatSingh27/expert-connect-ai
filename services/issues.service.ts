import { HttpError, apiRequest } from "./http";

export type IssueStatus = "open" | "ai_classified" | "waiting_for_assignment" | "assigned" | "accepted" | "in_progress" | "resolved" | "closed" | "submitted" | "operator_review" | "need_more_info" | "completed" | "rejected";
export type IssuePriority = "low" | "medium" | "high" | "critical";
export type IssueMedia = { id: string; url: string; type: "image" | "video" | "audio"; fileName: string };
export type AiResult = { detectedProblem?: string; category?: string; urgency?: string; confidence?: number; assignedExpert?: string; estimatedResponseTime?: string; priority?: IssuePriority };
export type Issue = {
  id: string | number; title: string; description: string; status: IssueStatus; priority?: IssuePriority; category?: string; problemType?: string; urgency?: string; requiredSkills?: string[]; confidenceScore?: number; aiExplanation?: string;
  preferredVisitDate?: string; preferredTime?: string; location?: string; address?: string; pinCode?: string;
  assignedExpertId?: string | number; assignedExpertName?: string; assignedOperatorId?: string | number; assignedOperatorName?: string;
  aiResult?: AiResult; media?:IssueMedia[]; attachments?: unknown[]; createdAt: string; updatedAt?: string;
};
export type ClassifyIssuePayload = { issueId?: string | number; title: string; description: string; location?: string; mediaIds?: string[] };
export type CreateIssuePayload = { title: string; description: string; category?: string; priority?: string; urgency?: string; requiredSkills?: string[]; preferredVisitDate?: string; preferredTime?: string; location: string; address: string; pinCode: string; mediaIds?: string[]; files?: File[] };

type RawAiResult = AiResult & { detected_problem?: string; assigned_expert?: string; estimated_response_time?: string; confidence_score?: number };
type RawIssue = Issue & Record<string, any>;
const CLASSIFY_ENDPOINTS = ["/issues/classify", "/ai/classify", "/classify"];
function normalizeAiResult(result: RawAiResult): AiResult {
  return { detectedProblem: result.detectedProblem ?? result.detected_problem ?? (result as any).problemType ?? (result as any).problem_type, category: result.category, urgency: result.urgency, confidence: result.confidence ?? result.confidence_score, assignedExpert: result.assignedExpert ?? result.assigned_expert, estimatedResponseTime: result.estimatedResponseTime ?? result.estimated_response_time, priority: result.priority };
}
function normalizeIssue(raw: RawIssue): Issue {
  const issue = { ...raw, problemType: raw.problemType ?? raw.problem_type, requiredSkills: raw.requiredSkills ?? raw.required_skills, confidenceScore: raw.confidenceScore ?? raw.confidence_score, aiExplanation: raw.aiExplanation ?? raw.ai_explanation, preferredVisitDate: raw.preferredVisitDate ?? raw.preferred_visit_date, preferredTime: raw.preferredTime ?? raw.preferred_time, pinCode: raw.pinCode ?? raw.pin_code, assignedExpertId: raw.assignedExpertId ?? raw.assigned_expert_id, assignedAt: raw.assignedAt ?? raw.assigned_at, createdAt: raw.createdAt ?? raw.created_at, updatedAt: raw.updatedAt ?? raw.updated_at } as Issue;
  issue.aiResult = issue.aiResult ?? normalizeAiResult({ category: issue.category, urgency: issue.urgency, priority: issue.priority, confidence: issue.confidenceScore, detectedProblem: issue.problemType });
  return issue;
}
function buildClassifyFormData(payload: ClassifyIssuePayload, files: File[]) {
  const formData = new FormData();
  formData.append("title", payload.title); formData.append("description", payload.description);
  if (payload.location) formData.append("location", payload.location);
  payload.mediaIds?.forEach((id) => formData.append("media_ids", id));
  files.forEach((file) => { formData.append("files", file); if (file.type.startsWith("image/")) formData.append("images", file); if (file.type.startsWith("video/")) formData.append("videos", file); if (file.type.startsWith("audio/")) formData.append("audio", file); });
  return formData;
}
function issueFormData(payload: Partial<CreateIssuePayload>, files: File[] = []) {
  const formData = new FormData();
  const append = (key: string, value: unknown) => { if (value !== undefined && value !== null && value !== "") formData.append(key, Array.isArray(value) ? value.join(", ") : String(value)); };
  append("title", payload.title); append("description", payload.description); append("category", payload.category); append("priority", payload.priority); append("urgency", payload.urgency); append("required_skills", payload.requiredSkills); append("preferred_visit_date", payload.preferredVisitDate); append("preferred_time", payload.preferredTime); append("location", payload.location); append("pin_code", payload.pinCode); append("address", payload.address);
  files.forEach((file) => formData.append("files", file));
  return formData;
}

export async function listIssues(params?: { status?: string; mine?: boolean; assignedToMe?: boolean }) {
  const query = new URLSearchParams();
  if (params?.status) query.set("status", params.status);
  if (params?.mine) query.set("mine", "true");
  if (params?.assignedToMe) query.set("assigned_to_me", "true");
  const rows = await apiRequest<RawIssue[]>(`/issues/${query.size ? `?${query}` : ""}`);
  return rows.map(normalizeIssue);
}
export async function classifyIssue(payload: ClassifyIssuePayload, files: File[] = []) {
  if (payload.issueId) return normalizeAiResult(await apiRequest<RawAiResult>(`/issues/${payload.issueId}/classify`, { method: "POST" }));
  let lastError: unknown;
  for (const endpoint of CLASSIFY_ENDPOINTS) {
    try {
      const raw = await apiRequest<RawAiResult>(endpoint, { method: "POST", body: files.length ? buildClassifyFormData(payload, files) : JSON.stringify(payload) });
      return normalizeAiResult(raw);
    } catch (error) { lastError = error; if (error instanceof HttpError && ![404, 405].includes(error.status)) throw error; }
  }
  throw lastError instanceof Error ? lastError : new Error("AI classification endpoint is not available");
}
export async function createIssue(payload: CreateIssuePayload) { return normalizeIssue(await apiRequest<RawIssue>("/issues/", { method: "POST", body: issueFormData(payload, payload.files ?? []) })); }
export async function getIssue(issueId: string | number) { return normalizeIssue(await apiRequest<RawIssue>(`/issues/${issueId}`)); }
export async function updateIssue(issueId: string | number, payload: Partial<CreateIssuePayload>) { return normalizeIssue(await apiRequest<RawIssue>(`/issues/${issueId}`, { method: "PUT", body: issueFormData(payload, payload.files ?? []) })); }
export function deleteIssue(issueId: string | number) { return apiRequest<{ message: string }>(`/issues/${issueId}`, { method: "DELETE" }); }
export function updateIssueStatus(issueId: string | number, status: IssueStatus) { return apiRequest<Issue>(`/experts/issues/${issueId}/status`, { method: "PATCH", body: JSON.stringify({ status }) }); }
export function updateIssuePriority(issueId: string | number, priority: IssuePriority) { return updateIssue(issueId, { priority }); }
export function assignIssue(issueId: string | number, expertId?: string | number) { return expertId ? apiRequest<Issue>(`/issues/${issueId}/assign`, { method: "POST", body: JSON.stringify({ expertId, expert_id: expertId }) }) : apiRequest<Issue>(`/issues/${issueId}/assign-best`, { method: "POST" }); }
export function getIssueMatches(issueId: string | number) { return apiRequest<Array<{ expert_id: number; full_name: string; score: number; skills?: string; service_area?: string }>>(`/issues/${issueId}/matches`); }
export async function assignOperator(issueId: string | number, operatorId: string | number) {
  try { return await apiRequest<Issue>(`/issues/${issueId}/assign-operator`, { method: "POST", body: JSON.stringify({ operatorId }) }); }
  catch (error) { if (error instanceof HttpError && [404, 405].includes(error.status)) return apiRequest<Issue>(`/admin/issues/${issueId}/assign-operator`, { method: "POST", body: JSON.stringify({ operatorId }) }); throw error; }
}
export function addIssueNote(issueId: string | number, note: string) { return apiRequest<Issue>(`/issues/${issueId}/notes`, { method: "POST", body: JSON.stringify({ note }) }); }
