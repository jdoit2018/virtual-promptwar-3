const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface RequestOptions extends RequestInit {
  token?: string;
}

export class APIError extends Error {
  status: number;
  detail: any;
  constructor(status: number, message: string, detail?: any) {
    super(message);
    this.status = status;
    this.detail = detail;
    this.name = "APIError";
  }
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const headers = new Headers(options.headers || {});
  
  // Try to retrieve token from options or localStorage
  let token = options.token;
  if (!token && typeof window !== "undefined") {
    token = localStorage.getItem("auth_token") || undefined;
  }

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const config: RequestInit = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);

    if (response.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("user_profile");
        // Redirect to login if in browser
        window.dispatchEvent(new Event("unauthorized-event"));
      }
      throw new APIError(401, "Session expired. Please log in again.");
    }

    if (!response.ok) {
      let detail = "An error occurred";
      try {
        const errorData = await response.json();
        detail = errorData.detail || JSON.stringify(errorData);
      } catch (_) {
        detail = await response.text();
      }
      throw new APIError(response.status, detail);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return await response.json() as T;
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    throw new APIError(500, error instanceof Error ? error.message : "Network error");
  }
}

export const api = {
  auth: {
    sync: () => request<any>("/api/auth/sync", { method: "POST" }),
  },
  users: {
    me: () => request<any>("/api/users/me"),
    exportData: () => request<any>("/api/users/me/export", { method: "POST" }),
    deleteAccount: () => request<any>("/api/users/me", { method: "DELETE" }),
  },
  baselines: {
    create: (quizResponses: any) => 
      request<any>("/api/baselines", {
        method: "POST",
        body: JSON.stringify({ quiz_responses: quizResponses }),
      }),
    getCurrent: () => request<any>("/api/baselines/current"),
  },
  logs: {
    create: (logData: {
      log_date: string;
      category: string;
      activity_type: string;
      quantity: number;
      metadata?: any;
    }) => 
      request<any>("/api/logs", {
        method: "POST",
        body: JSON.stringify(logData),
      }),
    get: (date: string) => request<any[]>(`/api/logs?log_date=${date}`),
    getWeeklySummary: (endDate: string) => 
      request<any>(`/api/logs/summary/weekly?end_date=${endDate}`),
  },
  goals: {
    create: (goalData: { target_co2e: number; target_year: number }) => 
      request<any>("/api/goals", {
        method: "POST",
        body: JSON.stringify(goalData),
      }),
    getActive: () => request<any>("/api/goals/active"),
  },
  challenges: {
    list: () => request<any[]>("/api/challenges"),
    start: (id: string) => request<any>(`/api/challenges/${id}/start`, { method: "POST" }),
    updateProgress: (id: string, progress: number) => 
      request<any>(`/api/challenges/${id}/progress`, {
        method: "PATCH",
        body: JSON.stringify({ progress }),
      }),
  },
  notifications: {
    registerToken: (token: string) => 
      request<any>("/api/notifications/register-token", {
        method: "POST",
        body: JSON.stringify({ token }),
      }),
  },
};
