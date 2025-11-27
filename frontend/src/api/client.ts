export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';

export interface ApiOptions {
  method?: HttpMethod;
  data?: any;
  headers?: Record<string, string>;
  token?: string | null;
  query?: Record<string, string | number | boolean | undefined | null>;
  isFormData?: boolean;
  skipAuth?: boolean;
}

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const buildQueryString = (query?: ApiOptions['query']) => {
  if (!query) return '';
  const params = new URLSearchParams();
  Object.entries(query).forEach(([key, value]) => {
    if (value === undefined || value === null || value === '') return;
    params.append(key, String(value));
  });
  const qs = params.toString();
  return qs ? `?${qs}` : '';
};

export async function apiFetch<T>(
  path: string,
  options: ApiOptions = {},
  fallbackToken?: string | null,
): Promise<T> {
  const {
    method = 'GET',
    data,
    headers = {},
    token,
    query,
    isFormData = false,
    skipAuth = false,
  } = options;

  const url = `${API_URL}${path}${buildQueryString(query)}`;
  const finalHeaders: Record<string, string> = { ...headers };
  let body: BodyInit | undefined;

  if (data !== undefined) {
    if (isFormData) {
      if (data instanceof FormData) {
        body = data;
      } else {
        const formData = new FormData();
        Object.entries(data).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            formData.append(key, value as any);
          }
        });
        body = formData;
      }
    } else {
      finalHeaders['Content-Type'] = 'application/json';
      body = JSON.stringify(data);
    }
  }

  const authToken = token ?? fallbackToken;
  if (authToken && !skipAuth) {
    finalHeaders.Authorization = `Bearer ${authToken}`;
  }

  const response = await fetch(url, {
    method,
    headers: finalHeaders,
    body,
  });

  const text = await response.text();
  let payload: any = null;
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = text;
    }
  }

  if (!response.ok) {
    const message =
      payload?.detail ||
      payload?.message ||
      payload?.error ||
      response.statusText ||
      'Request failed';
    throw new Error(message);
  }

  return payload as T;
}
