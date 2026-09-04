import { useCallback, useEffect, useRef, useState } from 'react'

// Browser-native speech-to-text (Web Speech API) — no library, no backend
// call. Chrome/Edge support it; Firefox/Safari don't, so `supported` lets
// callers hide the mic button entirely rather than show a dead control.
const SpeechRecognitionCtor: typeof window.SpeechRecognition | undefined =
  typeof window !== 'undefined' ? (window.SpeechRecognition ?? window.webkitSpeechRecognition) : undefined

// i18next language code -> BCP-47 locale tag the Web Speech API expects.
const SPEECH_LANG: Record<string, string> = {
  en: 'en-IN', hi: 'hi-IN', mr: 'mr-IN', bn: 'bn-IN', gu: 'gu-IN',
  kn: 'kn-IN', ml: 'ml-IN', pa: 'pa-IN', ta: 'ta-IN', te: 'te-IN',
}

export function useSpeechToText(language: string, onResult: (transcript: string) => void) {
  const [listening, setListening] = useState(false)
  const recognitionRef = useRef<InstanceType<NonNullable<typeof SpeechRecognitionCtor>> | null>(null)

  useEffect(() => () => recognitionRef.current?.stop(), [])

  const start = useCallback(() => {
    if (!SpeechRecognitionCtor || listening) return
    const recognition = new SpeechRecognitionCtor()
    recognition.lang = SPEECH_LANG[language] ?? 'en-IN'
    recognition.interimResults = false
    recognition.maxAlternatives = 1
    recognition.onresult = (e) => onResult(e.results[e.results.length - 1][0].transcript)
    recognition.onend = () => setListening(false)
    recognition.onerror = () => setListening(false)
    recognitionRef.current = recognition
    recognition.start()
    setListening(true)
  }, [language, listening, onResult])

  const stop = useCallback(() => {
    recognitionRef.current?.stop()
    setListening(false)
  }, [])

  return { supported: !!SpeechRecognitionCtor, listening, start, stop }
}
