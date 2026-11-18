import React, { useEffect, useRef, useState } from "react";
import { type ChatMessage } from "../api/client";
import { useVoice } from "../hooks/useVoice";
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

  const {
    isListening,
    isSpeaking,
    speechSupported,
    autoSpeakEnabled,
    voiceError,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    toggleAutoSpeak,
    clearVoiceError,
  } = useVoice({
    onTranscript: (liveTranscript) => {
      setInput(liveTranscript);
    },
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Auto-speak new assistant responses if enabled
  useEffect(() => {
    if (autoSpeakEnabled && messages.length > 0 && !isLoading) {
      const last = messages[messages.length - 1];
      if (last.role === "assistant") {
        speak(last.content);
      }
    }
  }, [messages, isLoading, autoSpeakEnabled, speak]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isListening) {
      stopListening();
    }
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
      {/* Voice & Assistant Header Bar */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "8px 16px",
          backgroundColor: "#ffffff",
          borderBottom: "1px solid #e2e8f0",
          fontSize: "12px",
          color: "#64748b",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <span>ShopEasy Hyderabad Support</span>
          {isSpeaking && (
            <span style={{ color: "#4f46e5", fontWeight: 600 }}>🔊 Speaking...</span>
          )}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {isSpeaking && (
            <button
              onClick={stopSpeaking}
              style={{
                background: "#fef2f2",
                border: "1px solid #fecaca",
                color: "#dc2626",
                borderRadius: "6px",
                padding: "2px 8px",
                cursor: "pointer",
                fontSize: "11px",
                fontWeight: 600,
              }}
            >
              Stop Audio
            </button>
          )}
          <button
            onClick={toggleAutoSpeak}
            title={autoSpeakEnabled ? "Auto-speak enabled" : "Click to auto-read answers"}
            style={{
              background: autoSpeakEnabled ? "#eef2ff" : "#f1f5f9",
              border: `1px solid ${autoSpeakEnabled ? "#c7d2fe" : "#cbd5e1"}`,
              color: autoSpeakEnabled ? "#4338ca" : "#64748b",
              borderRadius: "6px",
              padding: "3px 8px",
              cursor: "pointer",
              fontSize: "11px",
              fontWeight: 500,
              display: "flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            <span>{autoSpeakEnabled ? "🔊 Auto-Read On" : "🔈 Auto-Read Off"}</span>
          </button>
        </div>
      </div>

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
              Ask anything by typing or using the 🎙️ microphone button (returns, orders, cancellations, warranties).
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <MessageBubble
              key={msg.id}
              message={msg}
              onApprove={onApprove}
              isApproving={isApproving}
              onSpeak={speak}
              isSpeaking={isSpeaking}
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

        {/* Voice Error Banner */}
        {voiceError && (
          <div
            style={{
              padding: "10px 14px",
              borderRadius: "10px",
              backgroundColor: "#fff1f2",
              border: "1px solid #fecdd3",
              color: "#e11d48",
              fontSize: "13px",
              marginBottom: "16px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <span>🎙️ {voiceError}</span>
            <button
              onClick={clearVoiceError}
              style={{
                background: "transparent",
                border: "none",
                color: "#e11d48",
                cursor: "pointer",
                fontWeight: 600,
                fontSize: "16px",
              }}
            >
              ×
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Active Voice Listening Banner */}
      {isListening && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "8px 16px",
            backgroundColor: "#fef2f2",
            borderTop: "1px solid #fecaca",
            color: "#b91c1c",
            fontSize: "12px",
            fontWeight: 500,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={{ fontSize: "14px" }}>🔴</span>
            <span>Listening... Speak your question (e.g. "Can I return opened earbuds?")</span>
          </div>
          <button
            type="button"
            onClick={stopListening}
            style={{
              padding: "4px 10px",
              borderRadius: "6px",
              backgroundColor: "#dc2626",
              color: "#ffffff",
              border: "none",
              fontSize: "11px",
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Done
          </button>
        </div>
      )}

      {/* Input Form Bar */}
      <form
        onSubmit={handleSubmit}
        style={{
          display: "flex",
          gap: "8px",
          padding: "14px 18px",
          backgroundColor: "#ffffff",
          borderTop: isListening ? "none" : "1px solid #e2e8f0",
          alignItems: "center",
        }}
      >
        <div style={{ flex: 1, position: "relative", display: "flex", alignItems: "center" }}>
          <input
            ref={inputRef}
            type="text"
            value={input}
            maxLength={1000}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              isListening
                ? "Listening to your voice..."
                : "Ask about policies, order status, or click 🎙️ to speak..."
            }
            disabled={isLoading}
            style={{
              width: "100%",
              padding: "12px 64px 12px 16px",
              borderRadius: "10px",
              border: `1px solid ${isListening ? "#f87171" : "#cbd5e1"}`,
              outline: "none",
              fontSize: "14px",
              color: "#0f172a",
              backgroundColor: isLoading ? "#f1f5f9" : isListening ? "#fff5f5" : "#ffffff",
              boxSizing: "border-box",
            }}
          />
          {input.length > 50 && (
            <span
              style={{
                position: "absolute",
                right: "12px",
                fontSize: "11px",
                color: input.length > 900 ? "#dc2626" : "#94a3b8",
                fontWeight: 500,
                pointerEvents: "none",
              }}
            >
              {input.length}/1000
            </span>
          )}
        </div>

        {/* Microphone Button */}
        {speechSupported && (
          <button
            type="button"
            onClick={isListening ? stopListening : startListening}
            disabled={isLoading}
            title={isListening ? "Stop listening" : "Click to speak with voice"}
            style={{
              padding: "10px 14px",
              borderRadius: "10px",
              backgroundColor: isListening ? "#dc2626" : "#f1f5f9",
              color: isListening ? "#ffffff" : "#475569",
              border: `1px solid ${isListening ? "#b91c1c" : "#cbd5e1"}`,
              cursor: isLoading ? "not-allowed" : "pointer",
              fontSize: "16px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              transition: "all 0.2s ease",
              boxShadow: isListening ? "0 0 0 3px rgba(220, 38, 38, 0.25)" : "none",
            }}
          >
            {isListening ? "⏹️" : "🎙️"}
          </button>
        )}

        {/* Send Button */}
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
