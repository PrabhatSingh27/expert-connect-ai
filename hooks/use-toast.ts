"use client";
import { useCallback, useState } from "react";
import type { Toast } from "@/components/toast-stack";
export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const push = useCallback((message: string, type: Toast["type"] = "info") => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    setToasts((current) => [...current, { id, message, type }]);
    window.setTimeout(() => setToasts((current) => current.filter((toast) => toast.id !== id)), 4200);
  }, []);
  const close = useCallback((id: string) => setToasts((current) => current.filter((toast) => toast.id !== id)), []);
  return { toasts, toast: push, closeToast: close };
}
