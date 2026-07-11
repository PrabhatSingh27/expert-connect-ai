import { apiRequest } from "./http";
export type AvailabilitySlotPayload = { date: string; startTime: string; endTime: string; isAvailable: boolean };
export type AvailabilitySlot = AvailabilitySlotPayload & { id: string | number; expertId: string | number };
type RawSlot = AvailabilitySlot & Record<string, any>;
function normalizeSlot(slot: RawSlot): AvailabilitySlot {
  return { ...slot, startTime: slot.startTime ?? slot.start_time, endTime: slot.endTime ?? slot.end_time, isAvailable: slot.isAvailable ?? slot.is_available ?? true, expertId: slot.expertId ?? slot.expert_id };
}
function slotBody(payload: Partial<AvailabilitySlotPayload>) {
  return JSON.stringify({ date: payload.date, startTime: payload.startTime, start_time: payload.startTime, endTime: payload.endTime, end_time: payload.endTime, isAvailable: payload.isAvailable, is_available: payload.isAvailable });
}
export async function listAvailabilities(expertId?: string | number) { const q = expertId ? `?expertId=${encodeURIComponent(String(expertId))}` : ""; const rows = await apiRequest<RawSlot[]>(`/availability/${q}`); return rows.map(normalizeSlot); }
export async function createSlot(payload: AvailabilitySlotPayload) { return normalizeSlot(await apiRequest<RawSlot>("/availability/", { method: "POST", body: slotBody(payload) })); }
export async function getMyAvailabilities() { const rows = await apiRequest<RawSlot[]>("/availability/me"); return rows.map(normalizeSlot); }
export async function updateSlot(slotId: string | number, payload: Partial<AvailabilitySlotPayload>) { return normalizeSlot(await apiRequest<RawSlot>(`/availability/${slotId}`, { method: "PUT", body: slotBody(payload) })); }
export function deleteSlot(slotId: string | number) { return apiRequest<{ message: string }>(`/availability/${slotId}`, { method: "DELETE" }); }
