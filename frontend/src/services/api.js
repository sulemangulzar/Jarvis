const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || "/api"
).replace(/\/$/, "");

async function fetchWithTimeout(url, options = {}, timeoutMs = 8000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("Jarvis took too long to respond. Check the backend.");
    }
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

async function readResponse(response) {
  if (response.ok) {
    return response.json();
  }

  let message = "Something went wrong. Please try again.";
  try {
    const body = await response.json();
    if (typeof body.detail === "string") {
      message = body.detail;
    }
  } catch {
    // Keep the safe default message when the server did not return JSON.
  }

  throw new Error(message);
}

export function getMicrosoftLoginUrl() {
  return `${API_BASE_URL}/auth/microsoft/login`;
}

export async function getAuthStatus() {
  const response = await fetchWithTimeout(`${API_BASE_URL}/auth/status`, {
    method: "GET",
    credentials: "include",
    headers: {
      Accept: "application/json",
    },
  });

  return readResponse(response);
}

export async function logout() {
  const response = await fetchWithTimeout(`${API_BASE_URL}/auth/logout`, {
    method: "POST",
    credentials: "include",
    headers: {
      Accept: "application/json",
    },
  });

  return readResponse(response);
}

export async function sendChatMessage(message, conversationId = null) {
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC";
  const response = await fetchWithTimeout(
    `${API_BASE_URL}/chat`,
    {
      method: "POST",
      credentials: "include",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        timezone,
      }),
    },
    60_000,
  );

  return readResponse(response);
}
