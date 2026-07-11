import axios, { AxiosError, type AxiosProgressEvent } from "axios";
import { API_BASE_URL, getToken } from "./http";
import type { IssueMedia } from "./issues.service";

export type UploadProgressHandler = (progress: number) => void;
export type UploadOptions = { signal?: AbortSignal; onProgress?: UploadProgressHandler };
type RawUploadResponse = Record<string, any>;

function getErrorMessage(error: unknown) {
  if (axios.isCancel(error)) return "Upload cancelled";
  const axiosError = error as AxiosError<{ detail?: string; message?: string }>;
  return axiosError.response?.data?.message || axiosError.response?.data?.detail || axiosError.message || "Upload failed";
}
function unwrap(response: RawUploadResponse): RawUploadResponse {
  if ("data" in response && response.data) return unwrap(response.data);
  if ("file" in response && response.file) return unwrap(response.file);
  if ("media" in response && response.media) return Array.isArray(response.media) ? unwrap(response.media[0]) : unwrap(response.media);
  return response;
}
function normalize(response: RawUploadResponse, fallback: { type: IssueMedia["type"]; fileName: string }): IssueMedia {
  const raw = unwrap(response || {});
  return { id: raw.id || raw.media_id || raw.url || raw.file_url || fallback.fileName, url: raw.url || raw.file_url || "", type: raw.type || raw.media_type || fallback.type, fileName: raw.fileName || raw.file_name || raw.filename || fallback.fileName };
}
async function uploadMedia(endpoint: string, file: File, type: IssueMedia["type"], options: UploadOptions = {}) {
  const formData = new FormData(); formData.append("file", file);
  try {
    const response = await axios.post<RawUploadResponse>(`${API_BASE_URL}${endpoint}`, formData, { signal: options.signal, headers: { ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {}) }, onUploadProgress: (event: AxiosProgressEvent) => { if (!event.total) return; options.onProgress?.(Math.min(100, Math.round((event.loaded / event.total) * 100))); } });
    options.onProgress?.(100);
    return normalize(response.data, { type, fileName: file.name });
  } catch (error) { throw new Error(getErrorMessage(error)); }
}
export function uploadImage(file: File, options?: UploadOptions) { return uploadMedia("/upload/image", file, "image", options); }
export function uploadVideo(file: File, options?: UploadOptions) { return uploadMedia("/upload/video", file, "video", options); }
export function uploadAudio(file: File, options?: UploadOptions) { return uploadMedia("/upload/audio", file, "audio", options); }
