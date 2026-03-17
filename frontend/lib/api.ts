import {
  AdminSummary,
  ActionStatusResponse,
  AuthSessionResponse,
  DevMailMessage,
  JobRecord,
  PaginatedJobs,
  PlanDefinition,
  VisitorStatus
} from "@/lib/types";

const PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const INTERNAL_API_URL = process.env.API_URL_INTERNAL ?? PUBLIC_API_URL;

function getApiBaseUrl() {
  return typeof window === "undefined" ? INTERNAL_API_URL : PUBLIC_API_URL;
}

async function apiFetch(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);

  if (typeof window === "undefined") {
    const { cookies } = await import("next/headers");
    const cookieHeader = (await cookies()).toString();
    if (cookieHeader) {
      headers.set("cookie", cookieHeader);
    }
  }

  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers,
    credentials: "include",
    cache: init.cache ?? "no-store"
  });
  return response;
}

async function readErrorMessage(response: Response, fallback: string) {
  const body = await response.json().catch(() => ({}));
  return body.detail ?? body.message ?? fallback;
}

export async function createJob(
  endpoint: string,
  files: File[],
  fields: Record<string, string> = {}
) {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  Object.entries(fields).forEach(([key, value]) => formData.append(key, value));

  const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
    credentials: "include",
    method: "POST",
    body: formData
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response, "Something went wrong while creating the job."));
  }

  return (await response.json()) as JobRecord;
}

export async function fetchJob(jobId: string) {
  const response = await apiFetch(`/api/jobs/${jobId}`);
  if (!response.ok) throw new Error("Could not fetch job details.");
  return (await response.json()) as JobRecord;
}

export async function fetchJobs() {
  const response = await apiFetch("/api/jobs");
  if (!response.ok) throw new Error("Could not load jobs.");
  return (await response.json()) as JobRecord[];
}

export async function fetchJobsPage(params: {
  page?: number;
  pageSize?: number;
  status?: string;
  tool?: string;
  search?: string;
  mine?: boolean;
}) {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set("page", String(params.page));
  if (params.pageSize) searchParams.set("page_size", String(params.pageSize));
  if (params.status) searchParams.set("status", params.status);
  if (params.tool) searchParams.set("tool", params.tool);
  if (params.search) searchParams.set("search", params.search);
  if (params.mine) searchParams.set("mine", "true");

  const response = await apiFetch(`/api/jobs/history?${searchParams.toString()}`);
  if (!response.ok) throw new Error("Could not load paginated jobs.");
  return (await response.json()) as PaginatedJobs;
}

export async function fetchAdminSummary() {
  const response = await apiFetch("/api/admin/summary");
  if (!response.ok) throw new Error("Could not load admin summary.");
  return (await response.json()) as AdminSummary;
}

export async function signUp(payload: { email: string; password: string; full_name?: string }) {
  const response = await apiFetch("/api/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response, "Could not create your account."));
  }
  return (await response.json()) as AuthSessionResponse;
}

export async function logIn(payload: { email: string; password: string }) {
  const response = await apiFetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response, "Could not sign you in."));
  }
  return (await response.json()) as AuthSessionResponse;
}

export async function logOut() {
  const response = await apiFetch("/api/auth/logout", { method: "POST" });
  if (!response.ok) throw new Error("Could not sign you out.");
}

export async function fetchCurrentUser() {
  const response = await apiFetch("/api/auth/me");
  if (response.status === 401) return null;
  if (!response.ok) throw new Error("Could not load the current session.");
  return (await response.json()) as AuthSessionResponse;
}

export async function fetchPlans() {
  const response = await apiFetch("/api/billing/plans");
  if (!response.ok) throw new Error("Could not load plans.");
  const payload = (await response.json()) as { plans: PlanDefinition[] };
  return payload.plans;
}

export async function fetchVisitorStatus() {
  const response = await apiFetch("/api/visitor/status");
  if (!response.ok) throw new Error("Could not load visitor status.");
  return (await response.json()) as VisitorStatus;
}

export async function resendVerificationEmail(payload: { email?: string } = {}) {
  const response = await apiFetch("/api/auth/resend-verification", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response, "Could not send a new verification email."));
  }
  return (await response.json()) as ActionStatusResponse;
}

export async function verifyEmailToken(token: string) {
  const response = await apiFetch("/api/auth/verify-email", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token })
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response, "Could not verify your email."));
  }
  return (await response.json()) as ActionStatusResponse;
}

export async function requestPasswordReset(email: string) {
  const response = await apiFetch("/api/auth/forgot-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email })
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response, "Could not request a password reset."));
  }
  return (await response.json()) as ActionStatusResponse;
}

export async function resetPassword(token: string, password: string) {
  const response = await apiFetch("/api/auth/reset-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, password })
  });
  if (!response.ok) {
    throw new Error(await readErrorMessage(response, "Could not reset your password."));
  }
  return (await response.json()) as ActionStatusResponse;
}

export async function fetchLatestDevMail(email: string, kind: string) {
  const params = new URLSearchParams({ email, kind });
  const response = await apiFetch(`/api/auth/dev/messages/latest?${params.toString()}`);
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("Could not load the local mail preview.");
  return (await response.json()) as DevMailMessage;
}

export function resolveApiUrl(pathOrUrl: string) {
  if (/^https?:\/\//i.test(pathOrUrl)) {
    return pathOrUrl;
  }
  return `${PUBLIC_API_URL}${pathOrUrl.startsWith("/") ? pathOrUrl : `/${pathOrUrl}`}`;
}

export function getDownloadUrl(fileId: string) {
  return resolveApiUrl(`/downloads/${fileId}`);
}
