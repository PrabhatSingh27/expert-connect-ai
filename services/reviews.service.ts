import { apiRequest } from "./http";

export type ReviewPayload = { rating: number; review?: string };
export type Review = {
  id: string | number;
  issueId: string | number;
  expertId: string | number;
  customerId: string | number;
  rating: number;
  review?: string;
  comment?: string;
  createdAt: string;
};

export function getAverageRating(reviews: Array<{ rating?: number }> = []) {
  const ratings = reviews.map((item) => Number(item.rating)).filter((rating) => Number.isFinite(rating) && rating > 0);
  if (!ratings.length) return null;
  return Math.round((ratings.reduce((sum, rating) => sum + rating, 0) / ratings.length) * 10) / 10;
}

export function formatAverageRating(rating: number | null | undefined) {
  return typeof rating === "number" ? rating.toFixed(1) : "-";
}

function normalizeReview(raw: Review & Record<string, any>): Review {
  return {
    ...raw,
    issueId: raw.issueId ?? raw.issue_id,
    expertId: raw.expertId ?? raw.expert_id,
    customerId: raw.customerId ?? raw.customer_id,
    review: raw.review ?? raw.comment ?? raw.feedback ?? raw.message,
    comment: raw.comment ?? raw.review ?? raw.feedback ?? raw.message,
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
  const endpoints = [`/reviews/experts/${expertId}`, `/experts/${expertId}/reviews`, `/reviews/?expert_id=${expertId}`];
  let lastError: unknown;
  for (const endpoint of endpoints) {
    try {
      const rows = await apiRequest<Array<Review & Record<string, any>>>(endpoint);
      return rows.map(normalizeReview).filter((review) => String(review.expertId ?? expertId) === String(expertId));
    } catch (error) {
      lastError = error;
    }
  }
  throw lastError instanceof Error ? lastError : new Error("Expert reviews are not available");
}

export async function submitFeedback(issueId: string | number, payload: ReviewPayload) {
  return normalizeReview(await apiRequest<Review & Record<string, any>>("/feedback/", {
    method: "POST",
    body: JSON.stringify({ ...payload, issueId, issue_id: issueId }),
  }));
}
