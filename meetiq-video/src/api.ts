
const API_BASE_URL = "http://127.0.0.1:8000";

async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(
      `API request failed: ${response.status} ${response.statusText}`
    );
  }

  return response.json() as Promise<T>;
}

export function apiGet<T>(path: string): Promise<T> {
  return apiRequest<T>(path);
}

export function apiPost<T>(
  path: string,
  body: unknown
): Promise<T> {
  return apiRequest<T>(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
}

export function checkBackend(): Promise<unknown> {
  return apiGet("/");
}

export function getMeetings(): Promise<unknown> {
  return apiGet("/meetings");
}

export function getMeeting(
  meetingId: string | number
): Promise<unknown> {
  return apiGet(`/meetings/${meetingId}`);
}
