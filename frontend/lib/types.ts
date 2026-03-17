export type ToolSlug =
  | "upscale"
  | "background-remove"
  | "compress"
  | "pdf-merge"
  | "pdf-split"
  | "images-to-pdf";

export type ToolDefinition = {
  slug: ToolSlug;
  category: "Image" | "PDF";
  title: string;
  description: string;
  accept: string[];
  maxFiles: number;
  endpoint: string;
  badge: string;
  details: string;
  eta: string;
  supportsQualityMode?: boolean;
  available?: boolean;
  availabilityLabel?: string;
};

export type JobStatus = "queued" | "processing" | "completed" | "failed";

export type JobRecord = {
  id: string;
  user_id?: string | null;
  tool: string;
  status: JobStatus;
  created_at: string;
  updated_at: string;
  error?: string | null;
  input_files: string[];
  outputs: Array<{
    file_id: string;
    filename: string;
    size_bytes: number;
    content_type: string;
    share_url?: string | null;
    meta: Record<string, string | number | boolean | null>;
  }>;
  meta: Record<string, string | number | boolean | null>;
  progress: number;
  eta_seconds?: number | null;
};

export type AdminSummary = {
  total_jobs: number;
  failed_jobs: number;
  completed_jobs: number;
  queued_jobs: number;
  storage_usage_bytes: number;
  storage_breakdown?: Record<string, number>;
  processed_files: number;
  worker_threads?: number;
  queue_depth?: number;
  queue_groups?: number;
  oldest_queued_seconds?: number | null;
  jobs_by_tool?: Record<string, number>;
  cleanup?: Record<string, string | number | boolean | null>;
  auth?: {
    active_sessions?: number;
    pending_tokens?: Record<string, number>;
  };
  mail?: {
    message_count?: number;
    backend?: string;
  };
  system?: {
    platform?: string;
    python_version?: string;
    active_threads?: number;
  };
  recent_jobs: JobRecord[];
  runtime?: {
    torch_available: boolean;
    cuda_available: boolean;
    device: string;
    nvidia_smi_available?: boolean;
    gpu_name?: string;
    torch_version?: string;
  };
};

export type PaginatedJobs = {
  items: JobRecord[];
  total: number;
  page: number;
  page_size: number;
};

export type AuthUser = {
  id: string;
  email: string;
  full_name?: string | null;
  plan_key: string;
  email_verified: boolean;
  email_verified_at?: string | null;
  created_at: string;
};

export type UsageSummary = {
  month_start: string;
  jobs_used: number;
  jobs_limit?: number | null;
  jobs_remaining?: number | null;
};

export type AuthSessionResponse = {
  user: AuthUser;
  usage: UsageSummary;
  message?: string | null;
  requires_email_verification?: boolean;
  mail_preview_url?: string | null;
};

export type ActionStatusResponse = {
  success: boolean;
  message: string;
  mail_preview_url?: string | null;
};

export type DevMailMessage = {
  id: string;
  kind: string;
  to_email: string;
  subject: string;
  preview_url: string;
  action_url?: string | null;
  created_at: string;
};

export type PlanDefinition = {
  key: string;
  name: string;
  monthly_jobs?: number | null;
  monthly_price_usd: number;
  description: string;
  features: string[];
};

export type VisitorStatus = {
  mode: "anonymous" | "account";
  authenticated: boolean;
  user?: AuthSessionResponse;
  usage?: {
    jobs_used: number;
    jobs_limit: number;
    jobs_remaining: number;
  };
  upgrade?: {
    title: string;
    description: string;
    starting_price_usd: number;
  };
};
