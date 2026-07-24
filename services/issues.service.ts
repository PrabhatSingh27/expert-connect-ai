import { HttpError, apiRequest } from "./http";

export type IssueStatus = "open" | "ai_classified" | "waiting_for_assignment" | "assigned" | "accepted" | "in_progress" | "resolved" | "closed" | "submitted" | "operator_review" | "need_more_info" | "completed" | "rejected";
export type IssuePriority = "low" | "medium" | "high" | "critical";
export type IssueMedia = { id: string; url: string; type: "image" | "video" | "audio"; fileName: string };
export type IssueAttachment = { id?: string | number; fileUrl: string; fileType: string; fileName?: string; contentType?: string };
export type ExpertSummary = {
  id?: string | number;
  fullName?: string;
  name?: string;
  email?: string;
  phone?: string;
  skills?: string[] | string;
  serviceArea?: string;
  experienceYears?: number;
  rating?: number;
  isAvailable?: boolean;
};

export type AiResult = {
  detectedProblem?: string;
  category?: string;
  urgency?: string;
  confidence?: number;

  assignedExpert?: string;
  assignedExpertId?: string | number;

  expert?: ExpertSummary;

  estimatedResponseTime?: string;

  response?: string;
  responseStatus?: string;
  responseMessage?: string;

  priority?: IssuePriority;
};

export type Issue = {
  id: string | number; title: string; description: string; status: IssueStatus; priority?: IssuePriority; category?: string; problemType?: string; urgency?: string; requiredSkills?: string[]; confidenceScore?: number; aiExplanation?: string;
  preferredVisitDate?: string; preferredTime?: string; location?: string; address?: string; pinCode?: string;
  assignedExpertId?: string | number; assignedExpertName?: string; assignedOperatorId?: string | number; assignedOperatorName?: string;
  assignedExpert?: ExpertSummary; expert?: ExpertSummary;
  aiResult?: AiResult; media?:IssueMedia[]; attachments?: IssueAttachment[]; createdAt: string; updatedAt?: string;
};
export type ClassifyIssuePayload = { issueId?: string | number; title: string; description: string; location?: string; mediaIds?: string[] };
export type CreateIssuePayload = { title: string; description: string; category?: string; priority?: string; urgency?: string; requiredSkills?: string[]; preferredVisitDate?: string; preferredTime?: string; location: string; address: string; pinCode: string; mediaIds?: string[]; files?: File[] };
export type ChatMessage = { id: string | number; issueId?: string | number; senderId?: string | number; senderType?: string; message: string; createdAt?: string };
export type IssueDiagnosisPayload = { detectedProblem: string; response: string };

type RawAiResult = AiResult & Record<string, any> & { detected_problem?: string; assigned_expert?: string; estimated_response_time?: string; confidence_score?: number };
type RawIssue = Issue & Record<string, any>;
const CLASSIFY_ENDPOINTS = ["/issues/classify", "/ai/classify", "/classify"];
const DIAGNOSIS_STORAGE_KEY = "expert_connect_issue_diagnosis";

function getStoredDiagnoses(): Record<string, IssueDiagnosisPayload> {
  if (typeof window === "undefined") return {};
  try { return JSON.parse(window.localStorage.getItem(DIAGNOSIS_STORAGE_KEY) || "{}"); }
  catch { return {}; }
}

function getStoredDiagnosis(issueId: string | number) {
  return getStoredDiagnoses()[String(issueId)];
}

function saveStoredDiagnosis(issueId: string | number, payload: IssueDiagnosisPayload) {
  if (typeof window === "undefined") return;
  const rows = getStoredDiagnoses();
  rows[String(issueId)] = payload;
  window.localStorage.setItem(DIAGNOSIS_STORAGE_KEY, JSON.stringify(rows));
}

function applyDiagnosisOverride(issue: Issue) {
  const override = getStoredDiagnosis(issue.id);
  if (!override) return issue;
  issue.aiResult = {
    ...(issue.aiResult ?? {}),
    detectedProblem: override.detectedProblem || issue.aiResult?.detectedProblem,
    response: override.response || issue.aiResult?.response,
    responseMessage: override.response || issue.aiResult?.responseMessage,
  };
  issue.problemType = override.detectedProblem || issue.problemType;
  issue.aiExplanation = override.response || issue.aiExplanation;
  return issue;
}

function normalizeAiResult(result: RawAiResult): AiResult {
  const expert = result.expert ?? result.assignedExpertDetails ?? result.assigned_expert_details ?? result.assigned_expert;
  const expertName = typeof expert === "object" && expert ? expert.fullName ?? expert.full_name ?? expert.name : expert;
  return {
    detectedProblem: result.reasoning ?? result.detectedProblem ?? result.detected_problem ?? result.problemType ?? result.problem_type ?? result.detected ?? result.problem ?? result.issueType ?? result.issue_type ?? result.title,
    category: result.category ?? result.issueCategory ?? result.issue_category ?? result.serviceCategory ?? result.service_category,
    urgency: result.urgency ?? result.urgencyLevel ?? result.urgency_level,
    confidence: result.confidence ?? result.confidence_score ?? result.confidenceScore,
    assignedExpert: result.assignedExpert ?? result.assigned_expert_name ?? result.assignedExpertName ?? expertName,
    assignedExpertId: result.assignedExpertId ?? result.assigned_expert_id,
    expert: typeof expert === "object" ? expert : result.expert,
    estimatedResponseTime: result.estimatedResponseTime ?? result.estimated_response_time ?? result.responseTime ?? result.response_time ?? result.eta,
    response: result.thought_process ?? result.thoughtProcess ?? result.response ?? result.aiResponse ?? result.ai_response ?? result.recommendation ?? result.explanation ?? result.aiExplanation ?? result.ai_explanation,
    responseStatus: result.responseStatus ?? result.response_status ?? result.status,
    responseMessage: result.responseMessage ?? result.response_message ?? result.message,
    priority: result.priority,
  };
}
function normalizeIssue(raw: RawIssue): Issue {
  const rawExpert = raw.assignedExpert ?? raw.assigned_expert ?? raw.expert;
  const rawAttachments = raw.attachments ?? raw.media ?? raw.issue_attachments ?? raw.files ?? [];
  const attachments = Array.isArray(rawAttachments) ? rawAttachments.map((item: any) => ({
    id: item.id,
    fileUrl: item.fileUrl ?? item.file_url ?? item.url ?? item.path ?? "",
    fileType: item.fileType ?? item.file_type ?? item.type ?? item.contentType ?? item.content_type ?? "",
    fileName: item.fileName ?? item.file_name ?? item.name,
    contentType: item.contentType ?? item.content_type,
  })).filter((item: IssueAttachment) => item.fileUrl) : [];
  const assignedExpert = rawExpert ? {
    id: rawExpert.id,
    fullName: rawExpert.fullName ?? rawExpert.full_name ?? rawExpert.name,
    name: rawExpert.name,
    email: rawExpert.email,
    phone: rawExpert.phone ?? rawExpert.mobile ?? rawExpert.mobileNo ?? rawExpert.mobile_no,
    skills: rawExpert.skills,
    serviceArea: rawExpert.serviceArea ?? rawExpert.service_area,
    experienceYears: rawExpert.experienceYears ?? rawExpert.experience_years,
    rating: rawExpert.rating,
    isAvailable: rawExpert.isAvailable ?? rawExpert.is_available,
  } : undefined;
  const issue = { ...raw, problemType: raw.problemType ?? raw.problem_type, requiredSkills: raw.requiredSkills ?? raw.required_skills, confidenceScore: raw.confidenceScore ?? raw.confidence_score, aiExplanation: raw.aiExplanation ?? raw.ai_explanation, preferredVisitDate: raw.preferredVisitDate ?? raw.preferred_visit_date, preferredTime: raw.preferredTime ?? raw.preferred_time, pinCode: raw.pinCode ?? raw.pin_code, assignedExpertId: raw.assignedExpertId ?? raw.assigned_expert_id ?? assignedExpert?.id, assignedExpertName: raw.assignedExpertName ?? raw.assigned_expert_name ?? assignedExpert?.fullName ?? assignedExpert?.name, assignedExpert, expert: assignedExpert, assignedAt: raw.assignedAt ?? raw.assigned_at, attachments, createdAt: raw.createdAt ?? raw.created_at, updatedAt: raw.updatedAt ?? raw.updated_at } as Issue;
  const normalizedAi = normalizeAiResult({ ...(raw.aiResult ?? raw.ai_result ?? {}), category: issue.category, urgency: issue.urgency, priority: issue.priority, confidence: issue.confidenceScore, reasoning: raw.reasoning, thought_process: raw.thought_process, thoughtProcess: raw.thoughtProcess, detectedProblem: raw.reasoning ?? issue.problemType, assignedExpert: issue.assignedExpertName, assignedExpertId: issue.assignedExpertId, expert: assignedExpert, aiExplanation: issue.aiExplanation, response: raw.thought_process ?? raw.thoughtProcess ?? raw.response, responseStatus: raw.responseStatus ?? raw.response_status, estimatedResponseTime: raw.estimatedResponseTime ?? raw.estimated_response_time });
  const aiFromIssue = issue.aiResult ? normalizeAiResult(issue.aiResult as RawAiResult) : {};
  issue.aiResult = {
    ...normalizedAi,
    ...aiFromIssue,
    detectedProblem: aiFromIssue.detectedProblem ?? normalizedAi.detectedProblem,
    response: aiFromIssue.response ?? normalizedAi.response,
    responseMessage: aiFromIssue.responseMessage ?? normalizedAi.responseMessage,
  };
  return applyDiagnosisOverride(issue);
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
async function tryListIssues(endpoint: string) {
  const rows = await apiRequest<RawIssue[]>(endpoint);
  return rows.map(normalizeIssue);
}
function uniqueIssues(rows: Issue[]) {
  return Array.from(new Map(rows.map((issue) => [String(issue.id), issue])).values());
}
export async function listOperatorIssues() {
  const endpoints = [
    "/operator/issues",
    "/operator/issues/",
    "/issues/?status=submitted",
    "/issues/?status=operator_review",
    "/issues/?status=waiting_for_assignment",
    "/issues/",
  ];
  const results = await Promise.allSettled(endpoints.map((endpoint) => tryListIssues(endpoint)));
  const issues = results.flatMap((result) => result.status === "fulfilled" ? result.value : []);
  if (issues.length) return uniqueIssues(issues);
  return listIssues();
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
export function assignBestIssue(issueId: string | number) { return apiRequest<Issue>(`/issues/${issueId}/assign-best`, { method: "POST" }); }
export function assignIssueAsAdmin(issueId: string | number, expertId: string | number) { return apiRequest<Issue>(`/admin/issues/${issueId}/assign-expert`, { method: "PATCH", body: JSON.stringify({ expertId, expert_id: expertId }) }); }
export function assignIssueAsOperator(issueId: string | number, expertId: string | number) { return apiRequest<Issue>(`/operator/issues/${issueId}`, { method: "PATCH", body: JSON.stringify({ assignedExpertId: expertId, assigned_expert_id: expertId }) }); }
export function assignIssue(issueId: string | number, expertId?: string | number, role: "admin" | "operator" = "admin") { if (!expertId) return assignBestIssue(issueId); return role === "operator" ? assignIssueAsOperator(issueId, expertId) : assignIssueAsAdmin(issueId, expertId); }
export async function autoAssignIssueRoundRobin(issueId: string | number, experts: Array<{ id: string | number; isActive?: boolean; isVerified?: boolean }> = []) {
  const availableExperts = experts.filter((expert) => expert.id && expert.isActive !== false && expert.isVerified !== false);
  if (!availableExperts.length) return assignBestIssue(issueId);
  const key = "expert_connect_round_robin_index";
  const current = typeof window === "undefined" ? 0 : Number(window.localStorage.getItem(key) || "0");
  const expert = availableExperts[current % availableExperts.length];
  if (typeof window !== "undefined") window.localStorage.setItem(key, String((current + 1) % availableExperts.length));
  try { return await assignIssueAsOperator(issueId, expert.id); }
  catch (operatorError) {
    try { return await assignIssueAsAdmin(issueId, expert.id); }
    catch {
      try { return await assignBestIssue(issueId); }
      catch { throw operatorError; }
    }
  }
}
export function getIssueMatches(issueId: string | number) { return apiRequest<Array<{ expert_id: number; full_name: string; score: number; skills?: string; service_area?: string }>>(`/issues/${issueId}/matches`); }
export async function assignOperator(issueId: string | number, operatorId: string | number) {
  try { return await apiRequest<Issue>(`/issues/${issueId}/assign-operator`, { method: "POST", body: JSON.stringify({ operatorId }) }); }
  catch (error) { if (error instanceof HttpError && [404, 405].includes(error.status)) return apiRequest<Issue>(`/admin/issues/${issueId}/assign-operator`, { method: "POST", body: JSON.stringify({ operatorId }) }); throw error; }
}
export function addIssueNote(issueId: string | number, note: string) { return apiRequest<Issue>(`/issues/${issueId}/notes`, { method: "POST", body: JSON.stringify({ note }) }); }
export async function listIssueMessages(issueId: string | number) {
  const rows = await apiRequest<Array<Record<string, any>>>(`/issues/${issueId}/messages`);
  return rows.map((item) => ({
    id: item.id,
    issueId: item.issueId ?? item.issue_id,
    senderId: item.senderId ?? item.sender_id,
    senderType: item.senderType ?? item.sender_type,
    message: item.message ?? "",
    createdAt: item.createdAt ?? item.created_at,
  })) as ChatMessage[];
}
export function sendIssueMessage(issueId: string | number, message: string) {
  return apiRequest<ChatMessage>(`/issues/${issueId}/messages`, { method: "POST", body: JSON.stringify({ message }) });
}
export async function updateIssueDiagnosis(issueId: string | number, payload: IssueDiagnosisPayload) {
  const body = JSON.stringify({
    detectedProblem: payload.detectedProblem,
    detected_problem: payload.detectedProblem,
    expertDetectedProblem: payload.detectedProblem,
    expert_detected_problem: payload.detectedProblem,
    response: payload.response,
    expertResponse: payload.response,
    expert_response: payload.response,
    aiExplanation: payload.response,
    ai_explanation: payload.response,
  });
  const endpoints = [
    `/experts/issues/${issueId}/diagnosis`,
    `/experts/issues/${issueId}/response`,
    `/experts/issues/${issueId}/status`,
    `/issues/${issueId}`,
  ];
  let saved: Issue | null = null;
  for (const endpoint of endpoints) {
    try {
      saved = normalizeIssue(await apiRequest<RawIssue>(endpoint, { method: endpoint === `/issues/${issueId}` ? "PUT" : "PATCH", body }));
      break;
    } catch {
      saved = null;
    }
  }
  saveStoredDiagnosis(issueId, payload);
  return applyDiagnosisOverride(saved ?? ({ id: issueId, title: "", description: "", status: "submitted", createdAt: "", aiResult: {} } as Issue));
}
