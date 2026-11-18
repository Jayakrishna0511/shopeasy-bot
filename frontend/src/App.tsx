import { useEffect, useState } from "react";
import {
  approveAction,
  getHealth,
  getUsers,
  streamChatMessage,
  type ChatMessage,
  type Health,
  type UserProfile,
} from "./api/client";
import { ChatWindow } from "./components/ChatWindow";

const SUGGESTED_QUESTIONS = [
  "How long do I have to return an item?",
  "Can I return earbuds?",
  "Where is express delivery available?",
  "What should I do for error P-1042?",
];

export default function App() {
  const [health, setHealth] = useState<Health | null>(null);
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [currentUser, setCurrentUser] = useState<string>("ravi");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch((err) => {
      console.warn("Health check warning:", err);
    });
    getUsers().then(setUsers).catch((err) => {
      console.warn("Failed to load users:", err);
    });
  }, []);

  const handleUserChange = (newUserId: string) => {
    setCurrentUser(newUserId);
    setSessionId(null);
    setMessages([]);
  };

  const handleSendMessage = async (text: string) => {
    const userMessageId = `msg_${Date.now()}`;
    const userMessage: ChatMessage = {
      id: userMessageId,
      role: "user",
      content: text,
      createdAt: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    const botMessageId = `bot_${Date.now()}`;
    let hasCreatedBotBubble = false;

    try {
      await streamChatMessage(text, sessionId || undefined, currentUser, {
        onMeta: (meta) => {
          if (!sessionId) {
            setSessionId(meta.session_id);
          }
        },
        onToken: (token) => {
          if (!hasCreatedBotBubble) {
            hasCreatedBotBubble = true;
            setIsLoading(false);
            setMessages((prev) => [
              ...prev,
              {
                id: botMessageId,
                role: "assistant",
                content: token,
                createdAt: new Date().toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                }),
              },
            ]);
          } else {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === botMessageId
                  ? { ...msg, content: msg.content + token }
                  : msg
              )
            );
          }
        },
        onDone: (doneData) => {
          if (doneData.session_id && !sessionId) {
            setSessionId(doneData.session_id);
          }
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === botMessageId
                ? {
                    ...msg,
                    content: doneData.answer || msg.content,
                    sources: doneData.sources,
                    approvalRequired: doneData.approval_required,
                  }
                : msg
            )
          );
        },
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to get response from server.";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async (token: string) => {
    setIsApproving(true);
    setError(null);
    try {
      const res = await approveAction(token, sessionId || undefined, currentUser);
      // Remove approval card once confirmed
      setMessages((prev) =>
        prev.map((msg) => ({ ...msg, approvalRequired: undefined }))
      );
      // Add assistant confirmation message
      setMessages((prev) => [
        ...prev,
        {
          id: `bot_appr_${Date.now()}`,
          role: "assistant",
          content: `✅ ${res.message}`,
          createdAt: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        },
      ]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to approve cancellation.";
      setError(msg);
    } finally {
      setIsApproving(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "#f1f5f9",
        padding: "32px 16px",
        fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      }}
    >
      <div style={{ maxWidth: "760px", margin: "0 auto" }}>
        {/* Header Bar */}
        <header
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "20px",
            backgroundColor: "#ffffff",
            padding: "16px 24px",
            borderRadius: "16px",
            border: "1px solid #e2e8f0",
            boxShadow: "0 1px 3px rgba(0, 0, 0, 0.05)",
          }}
        >
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <span style={{ fontSize: "24px" }}>⚡</span>
              <h1 style={{ margin: 0, fontSize: "20px", fontWeight: 700, color: "#0f172a" }}>
                ShopEasy Support
              </h1>
            </div>
            <p style={{ margin: "2px 0 0 32px", fontSize: "12px", color: "#64748b" }}>
              Hyderabad, India • AI Customer Support with Grounded Citations
            </p>
          </div>

          {/* Right Controls: Customer Persona & Connection Status */}
          <div style={{ display: "flex", alignItems: "center", gap: "12px", flexWrap: "wrap" }}>
            {/* Customer Persona Selector */}
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <label htmlFor="user-select" style={{ fontSize: "12px", color: "#64748b", fontWeight: 500 }}>
                Customer:
              </label>
              <select
                id="user-select"
                value={currentUser}
                onChange={(e) => handleUserChange(e.target.value)}
                style={{
                  fontSize: "12px",
                  padding: "4px 8px",
                  borderRadius: "8px",
                  border: "1px solid #cbd5e1",
                  backgroundColor: "#f8fafc",
                  color: "#0f172a",
                  fontWeight: 600,
                  cursor: "pointer",
                  outline: "none",
                }}
              >
                {users.length > 0 ? (
                  users.map((u) => (
                    <option key={u.id} value={u.id}>
                      👤 {u.name} {u.is_premium ? "🌟 (Premium)" : ""}
                    </option>
                  ))
                ) : (
                  <>
                    <option value="ravi">👤 Ravi Kumar 🌟 (Premium)</option>
                    <option value="priya">👤 Priya Sharma</option>
                    <option value="arjun">👤 Arjun Reddy</option>
                  </>
                )}
              </select>
            </div>

            {/* Connection Status Pill */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                padding: "4px 10px",
                borderRadius: "20px",
                backgroundColor: health?.db === "up" ? "#ecfdf5" : "#fef2f2",
                border: `1px solid ${health?.db === "up" ? "#a7f3d0" : "#fecaca"}`,
                fontSize: "12px",
                fontWeight: 500,
                color: health?.db === "up" ? "#065f46" : "#991b1b",
              }}
            >
              <span
                style={{
                  width: "8px",
                  height: "8px",
                  borderRadius: "50%",
                  backgroundColor: health?.db === "up" ? "#10b981" : "#ef4444",
                }}
              />
              <span>{health?.db === "up" ? "System Online" : "Connecting..."}</span>
            </div>
          </div>
        </header>

        {/* Suggested Questions Quick Bar */}
        {messages.length === 0 && (
          <div style={{ marginBottom: "16px" }}>
            <div style={{ fontSize: "12px", fontWeight: 600, color: "#64748b", marginBottom: "8px" }}>
              SUGGESTED QUESTIONS:
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
              {SUGGESTED_QUESTIONS.map((q, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(q)}
                  disabled={isLoading}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "20px",
                    border: "1px solid #cbd5e1",
                    backgroundColor: "#ffffff",
                    color: "#334155",
                    fontSize: "13px",
                    cursor: "pointer",
                    transition: "all 0.15s ease",
                  }}
                  onMouseOver={(e) => (e.currentTarget.style.borderColor = "#6366f1")}
                  onMouseOut={(e) => (e.currentTarget.style.borderColor = "#cbd5e1")}
                >
                  💡 {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Chat Window Container */}
        <ChatWindow
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          error={error}
          onClearError={() => setError(null)}
          onApprove={handleApprove}
          isApproving={isApproving}
        />
      </div>
    </div>
  );
}
