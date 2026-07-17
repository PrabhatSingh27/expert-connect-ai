import { apiRequest } from "./http";
export type AvailabilitySlotPayload = { dayOfWeek: string; startTime: string; endTime: string };
export type AvailabilitySlot = AvailabilitySlotPayload & { id: string | number; expertId: string | number };
type RawSlot = AvailabilitySlot & Record<string, any>;
function normalizeSlot(slot: RawSlot): AvailabilitySlot {
  return { ...slot, dayOfWeek: slot.dayOfWeek ?? slot.day_of_week, startTime: slot.startTime ?? slot.start_time, endTime: slot.endTime ?? slot.end_time, expertId: slot.expertId ?? slot.expert_id };
}
function slotBody(payload: Partial<AvailabilitySlotPayload>) {
  return JSON.stringify({ day_of_week: payload.dayOfWeek, start_time: payload.startTime, end_time: payload.endTime });
}
export async function listAvailabilities(expertId?: string | number) { const q = expertId ? `?expertId=${encodeURIComponent(String(expertId))}` : ""; const rows = await apiRequest<RawSlot[]>(`/availability/${q}`); return rows.map(normalizeSlot); }
export async function createSlot(payload: AvailabilitySlotPayload) { return normalizeSlot(await apiRequest<RawSlot>("/availability/", { method: "POST", body: slotBody(payload) })); }
export async function getMyAvailabilities() { const rows = await apiRequest<RawSlot[]>("/availability/me"); return rows.map(normalizeSlot); }
export async function updateSlot(slotId: string | number, payload: Partial<AvailabilitySlotPayload>) { return normalizeSlot(await apiRequest<RawSlot>(`/availability/${slotId}`, { method: "PUT", body: slotBody(payload) })); }
export function deleteSlot(slotId: string | number) { return apiRequest<{ message: string }>(`/availability/${slotId}`, { method: "DELETE" }); }
