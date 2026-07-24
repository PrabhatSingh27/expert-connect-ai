export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://172.17.38.216:8000";

export function assetUrl(value?: string | null) {
  if (!value) return "";
  if (value.startsWith("blob:") || value.startsWith("data:") || /^https?:\/\//i.test(value)) return value;
  const base = API_BASE_URL.replace(/\/$/, "");
  const path = value.startsWith("/") ? value : `/${value}`;
  return `${base}${path}`;
}

export class HttpError extends Error {
  status: number;
  data: unknown;
  constructor(message: string, status: number, data?: unknown) {
    super(message);
    this.name = "HttpError";
    this.status = status;
    this.data = data;
  }
}

type ApiOptions = RequestInit & { auth?: boolean };

export function getToken() {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem("access_token") || localStorage.getItem("access_token") || localStorage.getItem("token");
}

export async function apiRequest<T>(endpoint: string, options: ApiOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  const token = getToken();
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (options.auth !== false && token) headers.set("Authorization", `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers });
  } catch {
    throw new HttpError("Network Error. Backend is not reachable.", 0);
  }

  const isJson = response.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await response.json().catch(() => null) : await response.text().catch(() => null);

  if (!response.ok) {
    const message = typeof data === "object" && data ? ((data as any).message || (data as any).detail) : undefined;
    throw new HttpError(message || `Request failed with ${response.status}`, response.status, data);
  }

  return data as T;
}
