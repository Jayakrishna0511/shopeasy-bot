import { useCallback, useEffect, useRef, useState } from "react";

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
  const [voiceError, setVoiceError] = useState<string | null>(null);

  // Keep latest callbacks in ref to avoid re-triggering effects and aborting recognition
  const callbacksRef = useRef<UseVoiceOptions>({ onTranscript, onAutoSubmit });
  useEffect(() => {
    callbacksRef.current = { onTranscript, onAutoSubmit };
  }, [onTranscript, onAutoSubmit]);

  const activeRecognitionRef = useRef<any>(null);

  // Check if browser supports speech recognition
  useEffect(() => {
    const win = window as unknown as IWindow;
    const SpeechRecognitionClass = win.SpeechRecognition || win.webkitSpeechRecognition;
    if (!SpeechRecognitionClass) {
      setSpeechSupported(false);
    }
  }, []);

  // Stop active speech recognition
  const stopListening = useCallback(() => {
    if (activeRecognitionRef.current) {
      try {
        activeRecognitionRef.current.stop();
      } catch {
        // ignore
      }
      activeRecognitionRef.current = null;
    }
    setIsListening(false);
  }, []);

  // Start fresh speech recognition session
  const startListening = useCallback(() => {
    setVoiceError(null);
    const win = window as unknown as IWindow;
    const SpeechRecognitionClass = win.SpeechRecognition || win.webkitSpeechRecognition;

    if (!SpeechRecognitionClass) {
      setVoiceError("Speech recognition is not supported in this browser. Please use Chrome, Edge, or Safari.");
      return;
    }

    // Stop any existing instance first
    if (activeRecognitionRef.current) {
      try {
        activeRecognitionRef.current.abort();
      } catch {
        // ignore
      }
    }

    try {
      const recognition = new SpeechRecognitionClass();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = "en-IN"; // English (India) default

      recognition.onstart = () => {
        setIsListening(true);
        setVoiceError(null);
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

        const currentText = (finalTranscript || interimTranscript).trim();
        if (currentText && callbacksRef.current.onTranscript) {
          callbacksRef.current.onTranscript(currentText);
        }

        if (finalTranscript && callbacksRef.current.onAutoSubmit) {
          callbacksRef.current.onAutoSubmit(finalTranscript.trim());
        }
      };

      recognition.onerror = (event: any) => {
        console.warn("Speech recognition error:", event.error);
        setIsListening(false);

        if (event.error === "not-allowed") {
          setVoiceError("Microphone permission denied. Please allow microphone access in your browser address bar.");
        } else if (event.error === "no-speech") {
          // User didn't say anything, benign
          setVoiceError(null);
        } else if (event.error === "network") {
          setVoiceError("Network error during speech recognition. Please check your connection.");
        } else {
          setVoiceError(`Voice error: ${event.error}`);
        }
      };

      recognition.onend = () => {
        setIsListening(false);
        activeRecognitionRef.current = null;
      };

      activeRecognitionRef.current = recognition;
      recognition.start();
    } catch (err: any) {
      console.error("Failed to start speech recognition:", err);
      setIsListening(false);
      setVoiceError("Could not start microphone. Please check browser permissions.");
    }
  }, []);

  // Text-To-Speech (TTS): Speak response aloud
  const speak = useCallback((text: string) => {
    if (!("speechSynthesis" in window)) return;

    window.speechSynthesis.cancel(); // Stop any ongoing speech

    // Clean markdown symbols, asterisks, headers, and citations [1] for natural speech
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
    utterance.lang = "en-IN";

    // Pick an English voice if available
    const voices = window.speechSynthesis.getVoices();
    if (voices.length > 0) {
      const englishVoice =
        voices.find((v) => v.lang.includes("en-IN") || v.lang.includes("en_IN")) ||
        voices.find((v) => v.lang.startsWith("en"));
      if (englishVoice) {
        utterance.voice = englishVoice;
      }
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

  const clearVoiceError = useCallback(() => {
    setVoiceError(null);
  }, []);

  return {
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
  };
}
