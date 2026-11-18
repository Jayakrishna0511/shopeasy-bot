export interface Health {
  status: string;
  db: string;
  pgvector: boolean;
}

export interface UserProfile {
  id: string;
  name: string;
  is_premium: boolean;
}

export interface ApprovalRequired {
  token: string;
  action: string;
  order_id: string;
  item: string;
  price: number;
  message: string;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  sources: string[];
  approval_required?: ApprovalRequired;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
  approvalRequired?: ApprovalRequired;
  createdAt: string;
}

export interface StreamCallbacks {
  onMeta?: (meta: { session_id: string }) => void;
  onToken: (token: string) => void;
  onDone?: (doneData: {
    session_id: string;
    answer: string;
    sources: string[];
    approval_required?: ApprovalRequired;
  }) => void;
}

export async function getHealth(): Promise<Health> {
  const res = await fetch("/api/health");
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

export async function getUsers(): Promise<UserProfile[]> {
  const res = await fetch("/api/auth/users");
  if (!res.ok) throw new Error("Failed to load users list");
  return res.json();
}

export async function getMe(userId?: string): Promise<UserProfile> {
  const headers: Record<string, string> = {};
  if (userId) headers["X-User-Id"] = userId;
  const res = await fetch("/api/auth/me", { headers });
  if (!res.ok) throw new Error("Failed to authenticate user");
  return res.json();
}

export async function sendChatMessage(
  message: string,
  sessionId?: string,
  userId?: string
): Promise<ChatResponse> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (userId) headers["X-User-Id"] = userId;

  const res = await fetch("/api/chat", {
    method: "POST",
    headers,
    body: JSON.stringify({ message, session_id: sessionId || null }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => null);
    throw new Error(errorData?.detail || `Server error (HTTP ${res.status})`);
  }
  return res.json();
}

export async function streamChatMessage(
  message: string,
  sessionId?: string,
  userId?: string,
  callbacks?: StreamCallbacks
): Promise<void> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "text/event-stream",
  };
  if (userId) headers["X-User-Id"] = userId;

  const res = await fetch("/api/chat/stream", {
    method: "POST",
    headers,
    body: JSON.stringify({ message, session_id: sessionId || null }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => null);
    throw new Error(errorData?.detail || `Server error (HTTP ${res.status})`);
  }

  const reader = res.body?.getReader();
  if (!reader) throw new Error("ReadableStream not supported in this browser.");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith(":")) continue;
      if (trimmed === "data: [DONE]") return;
      if (trimmed.startsWith("data:")) {
        try {
          const data = JSON.parse(trimmed.slice(5).trim());
          if (data.type === "meta" && callbacks?.onMeta) {
            callbacks.onMeta(data);
          } else if (data.type === "token" && callbacks?.onToken) {
            callbacks.onToken(data.token);
          } else if (data.type === "done" && callbacks?.onDone) {
            callbacks.onDone(data);
          }
        } catch {
          // ignore partial parse error
        }
      }
    }
  }
}

export async function approveAction(
  token: string,
  sessionId?: string,
  userId?: string
): Promise<{ success: boolean; message: string }> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (userId) headers["X-User-Id"] = userId;

  const res = await fetch("/api/approve", {
    method: "POST",
    headers,
    body: JSON.stringify({ token, session_id: sessionId || null }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || `Approval failed (HTTP ${res.status})`);
  }
  return res.json();
}
