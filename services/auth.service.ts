import { apiRequest, assetUrl } from "./http";

export type UserRole = "admin" | "operator" | "customer" | "expert" | "technician";
export type AuthUser = { id: string | number; name: string; email: string; role: UserRole; phone?: string; phone_number?: string; avatarUrl?: string; profileImageUrl?: string; profile_image_url?: string; accountType?: string; isExpert?: boolean; isAdmin?: boolean; isVerified?: boolean };
export type RegisterPayload = { name: string; email: string; password: string; phoneNumber?: string; role?: UserRole; photo?: File };
export type UpdateUserProfilePayload = { name?: string; email?: string; phone?: string; profileImage?: File };
export type LoginPayload = { email: string; password: string };
export type LoginResponse = { access_token?: string; accessToken?: string; token?: string; token_type?: string; tokenType?: string; user?: AuthUser; role?: UserRole; accountType?: string; isExpert?: boolean; isAdmin?: boolean; name?: string };

function normalizeUser(raw: AuthUser & Record<string, any>): AuthUser {
  const profileImageUrl = assetUrl(raw.profileImageUrl ?? raw.profile_image_url ?? raw.avatarUrl ?? raw.avatar_url ?? raw.photoUrl ?? raw.photo_url);
  return { ...raw, phone: raw.phone ?? raw.phone_number, profileImageUrl, profile_image_url: profileImageUrl, avatarUrl: profileImageUrl };
}

export function register(payload: RegisterPayload) {
  const body = new FormData();
  body.append("name", payload.name);
  body.append("email", payload.email);
  body.append("password", payload.password);
  if (payload.phoneNumber) body.append("phone_number", payload.phoneNumber);
  if (payload.role) body.append("role", payload.role);
  if (payload.photo) body.append("photo", payload.photo);
  return apiRequest<AuthUser & Record<string, any>>("/auth/register", { method: "POST", body, auth: false }).then(normalizeUser);
}
export function login(payload: LoginPayload) {
  return apiRequest<LoginResponse>("/auth/login", { method: "POST", body: JSON.stringify(payload), auth: false });
}
export function getMe() { return apiRequest<AuthUser & Record<string, any>>("/auth/me").then(normalizeUser); }
export function updateMe(payload: UpdateUserProfilePayload) {
  const body = new FormData();
  if (payload.name) body.append("name", payload.name);
  if (payload.email) body.append("email", payload.email);
  if (payload.phone) body.append("phone_number", payload.phone);
  if (payload.profileImage) {
    body.append("photo", payload.profileImage);
    body.append("profile_image", payload.profileImage);
  }
  return apiRequest<AuthUser & Record<string, any>>("/users/profile/me", { method: "PUT", body }).then(normalizeUser);
}
export function forgotPassword(email: string) { return apiRequest<{ message: string }>("/auth/forgot-password", { method: "POST", body: JSON.stringify({ email }), auth: false }); }
export function resetPassword(token: string, password: string) { return apiRequest<{ message: string }>("/auth/reset-password", { method: "POST", body: JSON.stringify({ token, password }), auth: false }); }
export function saveSession(response: LoginResponse) {
  const token = response.access_token || response.accessToken || response.token;
  if (token) sessionStorage.setItem("access_token", token);
  if (response.user?.role || response.role) sessionStorage.setItem("role", response.user?.role || response.role!);
  if (response.accountType || response.user?.accountType) sessionStorage.setItem("account_type", response.accountType || response.user?.accountType || "");
}
export function clearSession() { sessionStorage.removeItem("access_token"); sessionStorage.removeItem("role"); sessionStorage.removeItem("account_type"); localStorage.removeItem("token"); }
