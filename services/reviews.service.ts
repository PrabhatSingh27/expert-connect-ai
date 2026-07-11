import { apiRequest } from "./http";

export type ReviewPayload = { rating: number; review?: string };
export type Review = {
  id: string | number;
  issueId: string | number;
  expertId: string | number;
  customerId: string | number;
  rating: number;
  review?: string;
  createdAt: string;
};

function normalizeReview(raw: Review & Record<string, any>): Review {
  return {
    ...raw,
    issueId: raw.issueId ?? raw.issue_id,
    expertId: raw.expertId ?? raw.expert_id,
    customerId: raw.customerId ?? raw.customer_id,
    createdAt: raw.createdAt ?? raw.created_at,
  };
}

export async function submitReview(issueId: string | number, payload: ReviewPayload) {
  return normalizeReview(await apiRequest<Review & Record<string, any>>(`/reviews/issues/${issueId}`, {
    method: "POST",
    body: JSON.stringify(payload),
  }));
}

export async function listExpertReviews(expertId: string | number) {
  const rows = await apiRequest<Array<Review & Record<string, any>>>(`/reviews/experts/${expertId}`);
  return rows.map(normalizeReview);
}

export async function submitFeedback(issueId: string | number, payload: ReviewPayload) {
  return normalizeReview(await apiRequest<Review & Record<string, any>>("/feedback/", {
    method: "POST",
    body: JSON.stringify({ ...payload, issueId, issue_id: issueId }),
  }));
}
