import React from "react";
import { type ChatMessage } from "../api/client";

interface MessageBubbleProps {
  message: ChatMessage;
  onApprove?: (token: string) => void;
  isApproving?: boolean;
  onSpeak?: (text: string) => void;
  isSpeaking?: boolean;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({
  message,
  onApprove,
  isApproving,
  onSpeak,
  isSpeaking,
}) => {
  const isUser = message.role === "user";

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: "16px",
      }}
    >
      <div
        style={{
          maxWidth: "80%",
          display: "flex",
          flexDirection: "column",
          alignItems: isUser ? "flex-end" : "flex-start",
        }}
      >
        <div
          style={{
            fontSize: "11px",
            color: "#64748b",
            marginBottom: "4px",
            display: "flex",
            alignItems: "center",
            gap: "6px",
          }}
        >
          <span>{isUser ? "You" : "🤖 ShopEasy Assistant"}</span>
          <span>•</span>
          <span>{message.createdAt}</span>
          {!isUser && onSpeak && (
            <button
              onClick={() => onSpeak(message.content)}
              title="Read aloud"
              style={{
                background: "transparent",
                border: "none",
                cursor: "pointer",
                padding: "0 2px",
                fontSize: "12px",
                opacity: 0.7,
                display: "inline-flex",
                alignItems: "center",
              }}
              onMouseEnter={(e) => ((e.target as HTMLElement).style.opacity = "1")}
              onMouseLeave={(e) => ((e.target as HTMLElement).style.opacity = "0.7")}
            >
              🔊
            </button>
          )}
        </div>

        <div
          style={{
            padding: "12px 16px",
            borderRadius: isUser ? "16px 16px 2px 16px" : "16px 16px 16px 2px",
            backgroundColor: isUser ? "#4f46e5" : "#ffffff",
            color: isUser ? "#ffffff" : "#1e293b",
            boxShadow: isUser
              ? "0 2px 4px rgba(79, 70, 229, 0.15)"
              : "0 1px 3px rgba(0, 0, 0, 0.08), 0 1px 2px rgba(0, 0, 0, 0.04)",
            border: isUser ? "none" : "1px solid #e2e8f0",
            fontSize: "14px",
            lineHeight: "1.55",
            wordBreak: "break-word",
            whiteSpace: "pre-wrap",
          }}
        >
          {message.content}

          {/* Cancellation Human Approval Card */}
          {!isUser && message.approvalRequired && (
            <div
              style={{
                marginTop: "12px",
                padding: "12px",
                borderRadius: "10px",
                backgroundColor: "#fff7ed",
                border: "1px solid #fed7aa",
                color: "#7c2d12",
              }}
            >
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  fontWeight: 700,
                  fontSize: "13px",
                  marginBottom: "4px",
                }}
              >
                <span>⚠️</span>
                <span>Confirm Order Cancellation</span>
              </div>
              <div style={{ fontSize: "12px", lineHeight: "1.4", marginBottom: "10px" }}>
                Order #{message.approvalRequired.order_id} ({message.approvalRequired.item}) • Refund: ₹{message.approvalRequired.price}
              </div>
              <button
                onClick={() => onApprove && onApprove(message.approvalRequired!.token)}
                disabled={isApproving}
                style={{
                  padding: "6px 14px",
                  borderRadius: "8px",
                  backgroundColor: "#dc2626",
                  color: "#ffffff",
                  border: "none",
                  fontSize: "12px",
                  fontWeight: 600,
                  cursor: isApproving ? "not-allowed" : "pointer",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "6px",
                  boxShadow: "0 1px 2px rgba(0, 0, 0, 0.1)",
                }}
              >
                {isApproving ? "Processing Cancellation..." : "Confirm Cancel Order"}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
