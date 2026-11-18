import React, { useEffect, useRef, useState } from "react";
import { type ChatMessage } from "../api/client";
import { MessageBubble } from "./MessageBubble";

interface ChatWindowProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  error: string | null;
  onClearError?: () => void;
  onApprove?: (token: string) => void;
  isApproving?: boolean;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  onSendMessage,
  isLoading,
  error,
  onClearError,
  onApprove,
  isApproving,
}) => {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const cleanText = input.trim();
    if (!cleanText || isLoading) return;

    if (onClearError) onClearError();
    onSendMessage(cleanText);
    setInput("");
    inputRef.current?.focus();
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "600px",
        backgroundColor: "#f8fafc",
        borderRadius: "16px",
        border: "1px solid #e2e8f0",
        overflow: "hidden",
        boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.03)",
      }}
    >
      {/* Chat Messages Scroll Container */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "20px",
        }}
      >
        {messages.length === 0 ? (
          <div
            style={{
              height: "100%",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              color: "#94a3b8",
              textAlign: "center",
              padding: "20px",
            }}
          >
            <div style={{ fontSize: "40px", marginBottom: "12px" }}>🛍️</div>
            <div style={{ fontWeight: 600, fontSize: "16px", color: "#475569", marginBottom: "4px" }}>
              Welcome to ShopEasy Support
            </div>
            <div style={{ fontSize: "13px", maxWidth: "340px", lineHeight: "1.5" }}>
              Ask anything about returns, shipping, cancellations, warranty, or payment errors.
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              onApprove={onApprove}
              isApproving={isApproving}
            />
          ))
        )}

        {/* Loading Indicator */}
        {isLoading && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              color: "#64748b",
              fontSize: "13px",
              padding: "8px 16px",
              backgroundColor: "#ffffff",
              borderRadius: "12px",
              border: "1px solid #e2e8f0",
              width: "fit-content",
              boxShadow: "0 1px 2px rgba(0, 0, 0, 0.05)",
              marginBottom: "16px",
            }}
          >
            <span style={{ display: "inline-block", animation: "spin 1s linear infinite" }}>⏳</span>
            <span>Searching ShopEasy policies & generating answer...</span>
          </div>
        )}

        {/* Error Banner */}
        {error && (
          <div
            style={{
              padding: "10px 14px",
              borderRadius: "10px",
              backgroundColor: "#fef2f2",
              border: "1px solid #fecaca",
              color: "#b91c1c",
              fontSize: "13px",
              marginBottom: "16px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span>⚠️ {error}</span>
            {onClearError && (
              <button
                onClick={onClearError}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#b91c1c",
                  cursor: "pointer",
                  fontWeight: 600,
                  fontSize: "16px",
                }}
              >
                ×
              </button>
            )}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form Bar */}
      <form
        onSubmit={handleSubmit}
        style={{
          display: "flex",
          gap: "10px",
          padding: "14px 18px",
          backgroundColor: "#ffffff",
          borderTop: "1px solid #e2e8f0",
          alignItems: "center",
        }}
      >
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about policy, shipping, or returns..."
          disabled={isLoading}
          style={{
            flex: 1,
            padding: "12px 16px",
            borderRadius: "10px",
            border: "1px solid #cbd5e1",
            outline: "none",
            fontSize: "14px",
            color: "#0f172a",
            backgroundColor: isLoading ? "#f1f5f9" : "#ffffff",
          }}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          style={{
            padding: "12px 20px",
            borderRadius: "10px",
            backgroundColor: isLoading || !input.trim() ? "#cbd5e1" : "#4f46e5",
            color: "#ffffff",
            border: "none",
            fontWeight: 600,
            fontSize: "14px",
            cursor: isLoading || !input.trim() ? "not-allowed" : "pointer",
            transition: "background-color 0.2s ease",
          }}
        >
          Send
        </button>
      </form>
    </div>
  );
};
