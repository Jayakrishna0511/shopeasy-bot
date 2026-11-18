import { useCallback, useEffect, useRef, useState } from "react";

// Web Speech API interface definitions for TypeScript
interface IWindow extends Window {
  SpeechRecognition?: any;
  webkitSpeechRecognition?: any;
}

interface UseVoiceOptions {
  onTranscript?: (transcript: string) => void;
  onAutoSubmit?: (transcript: string) => void;
}

export function useVoice({ onTranscript, onAutoSubmit }: UseVoiceOptions = {}) {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [speechSupported, setSpeechSupported] = useState(true);
  const [autoSpeakEnabled, setAutoSpeakEnabled] = useState(false);

  const recognitionRef = useRef<any>(null);

  // Check browser support on mount
  useEffect(() => {
    const win = window as unknown as IWindow;
    const SpeechRecognitionClass = win.SpeechRecognition || win.webkitSpeechRecognition;

    if (!SpeechRecognitionClass) {
      setSpeechSupported(false);
      return;
    }

    const recognition = new SpeechRecognitionClass();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = "en-IN"; // English (India) default for ShopEasy Hyderabad

    recognition.onstart = () => {
      setIsListening(true);
    };

    recognition.onresult = (event: any) => {
      let interimTranscript = "";
      let finalTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }

      const currentText = finalTranscript || interimTranscript;
      if (currentText && onTranscript) {
        onTranscript(currentText);
      }

      if (finalTranscript && onAutoSubmit) {
        onAutoSubmit(finalTranscript.trim());
      }
    };

    recognition.onerror = (event: any) => {
      console.warn("Speech recognition error:", event.error);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      try {
        recognition.abort();
      } catch {
        // ignore
      }
    };
  }, [onTranscript, onAutoSubmit]);

  // Start speech recognition
  const startListening = useCallback(() => {
    if (!recognitionRef.current) {
      alert("Speech recognition is not supported in this browser. Please use Chrome or Edge.");
      return;
    }
    try {
      recognitionRef.current.start();
    } catch (e) {
      // If already started, stop and restart
      recognitionRef.current.stop();
    }
  }, []);

  // Stop speech recognition
  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // ignore
      }
      setIsListening(false);
    }
  }, []);

  // Text-To-Speech (TTS): Speak response aloud
  const speak = useCallback((text: string) => {
    if (!("speechSynthesis" in window)) return;

    window.speechSynthesis.cancel(); // Stop any ongoing speech

    // Clean markdown symbols, asterisks, and citations [1] for natural speech
    const cleanSpeechText = text
      .replace(/\[\d+\]/g, "")
      .replace(/\*\*(.*?)\*\*/g, "$1")
      .replace(/\*(.*?)\*/g, "$1")
      .replace(/#{1,6}\s+/g, "")
      .replace(/`{1,3}.*?`{1,3}/g, "")
      .trim();

    if (!cleanSpeechText) return;

    const utterance = new SpeechSynthesisUtterance(cleanSpeechText);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    // Pick an English voice if available
    const voices = window.speechSynthesis.getVoices();
    const englishVoice =
      voices.find((v) => v.lang.includes("en-IN") || v.lang.includes("en_IN")) ||
      voices.find((v) => v.lang.startsWith("en"));
    if (englishVoice) {
      utterance.voice = englishVoice;
    }

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    window.speechSynthesis.speak(utterance);
  }, []);

  const stopSpeaking = useCallback(() => {
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
    }
  }, []);

  const toggleAutoSpeak = useCallback(() => {
    setAutoSpeakEnabled((prev) => !prev);
  }, []);

  return {
    isListening,
    isSpeaking,
    speechSupported,
    autoSpeakEnabled,
    startListening,
    stopListening,
    speak,
    stopSpeaking,
    toggleAutoSpeak,
  };
}
