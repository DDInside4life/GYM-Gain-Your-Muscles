import { API_URL } from "./constants";

type FetchOpts = RequestInit & { auth?: boolean };

const TOKEN_KEY = "gym.tokens";

export type Tokens = { access_token: string; refresh_token: string };

type ApiErrorPayload = {
  error_code?: string;
  message?: string;
  context?: unknown;
  detail?: unknown;
};

const FRIENDLY_ERROR_MESSAGES: Record<string, string> = {
  internal_error: "Сервис временно недоступен. Попробуйте еще раз.",
  invalid_request: "Проверьте введенные данные и повторите попытку.",
  resource_not_found: "Запрошенные данные не найдены.",
  auth_unauthorized: "Нужно войти в аккаунт снова.",
  access_forbidden: "У вас нет доступа к этому действию.",
  state_conflict: "Операция не может быть выполнена в текущем состоянии данных.",
  rate_limited: "Слишком много запросов. Попробуйте чуть позже.",
};

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public detail?: unknown,
    public errorCode?: string,
    public context?: unknown,
  ) {
    super(message);
  }
}

export const tokenStore = {
  get(): Tokens | null {
    if (typeof window === "undefined") return null;
    try {
      const raw = window.localStorage.getItem(TOKEN_KEY);
      return raw ? (JSON.parse(raw) as Tokens) : null;
    } catch {
      return null;
    }
  },
  set(t: Tokens) {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(TOKEN_KEY, JSON.stringify(t));
    window.dispatchEvent(new CustomEvent("gym:auth"));
  },
  clear() {
    if (typeof window === "undefined") return;
    window.localStorage.removeItem(TOKEN_KEY);
    window.dispatchEvent(new CustomEvent("gym:auth"));
  },
};

let refreshing: Promise<Tokens | null> | null = null;

function refresh(): Promise<Tokens | null> {
  if (refreshing) return refreshing;
  refreshing = (async () => {
    try {
      const t = tokenStore.get();
      if (!t?.refresh_token) return null;
      const res = await fetch(`${API_URL}/auth/refresh`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ refresh_token: t.refresh_token }),
      });
      if (!res.ok) {
        tokenStore.clear();
        return null;
      }
      const data = (await res.json()) as Tokens;
      tokenStore.set(data);
      return data;
    } finally {
      refreshing = null;
    }
  })();
  return refreshing;
}

async function parseError(res: Response): Promise<ApiError> {
  const text = await res.text();
  let detail: unknown = text;
  let payload: ApiErrorPayload | null = null;
  try {
    const parsed = JSON.parse(text);
    payload = parsed as ApiErrorPayload;
    detail = parsed?.detail ?? parsed;
  } catch {
    /* not json */
  }
  const errorCode = payload?.error_code;
  const messageFromApi = payload?.message;
  const fallback = typeof detail === "string" ? detail : res.statusText || `HTTP ${res.status}`;
  const msg = (errorCode && FRIENDLY_ERROR_MESSAGES[errorCode]) || messageFromApi || fallback;
  return new ApiError(res.status, msg, detail, errorCode, payload?.context);
}

export async function api<T = unknown>(path: string, opts: FetchOpts = {}): Promise<T> {
  const { auth = false, headers, ...rest } = opts;
  const h = new Headers(headers);
  if (!h.has("content-type") && rest.body) h.set("content-type", "application/json");
  if (auth) {
    const t = tokenStore.get();
    if (t?.access_token) h.set("authorization", `Bearer ${t.access_token}`);
  }

  let res = await fetch(`${API_URL}${path}`, { ...rest, headers: h });
  if (res.status === 401 && auth) {
    const fresh = await refresh();
    if (fresh) {
      h.set("authorization", `Bearer ${fresh.access_token}`);
      res = await fetch(`${API_URL}${path}`, { ...rest, headers: h });
    }
  }
  if (!res.ok) throw await parseError(res);
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
