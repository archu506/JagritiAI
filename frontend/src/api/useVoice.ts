import { useState, useCallback, useRef } from "react";
import type { Lang } from "../context/I18nContext";

const SPEECH_LANG_MAP: Record<Lang, string> = {
  en: "en-IN",
  hi: "hi-IN",
  or: "or-IN",
};

export function useVoice(lang: Lang) {
  const [listening, setListening] = useState(false);
  const [supported] = useState(
    () => typeof window !== "undefined" && ("SpeechRecognition" in window || "webkitSpeechRecognition" in window)
  );
  const recognitionRef = useRef<any>(null);

  const startListening = useCallback((onResult: (text: string) => void) => {
    if (!supported) return;
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = SPEECH_LANG_MAP[lang];
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onresult = (event: any) => {
      const text = event.results[0][0].transcript;
      onResult(text);
    };
    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);

    recognitionRef.current = recognition;
    setListening(true);
    recognition.start();
  }, [lang, supported]);

  const stopListening = useCallback(() => {
    recognitionRef.current?.stop();
    setListening(false);
  }, []);

  const speak = useCallback((text: string) => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = SPEECH_LANG_MAP[lang];
    window.speechSynthesis.cancel();
    window.speechSynthesis.speak(utterance);
  }, [lang]);

  return { supported, listening, startListening, stopListening, speak };
}
