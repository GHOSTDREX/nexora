// Minimal ambient types for the Web Speech API — not part of TypeScript's
// standard DOM lib. Only the bits useSpeechToText.ts actually uses.
interface SpeechRecognitionResult {
  0: { transcript: string }
}

interface SpeechRecognitionEvent {
  results: { length: number; [index: number]: SpeechRecognitionResult }
}

interface SpeechRecognition extends EventTarget {
  lang: string
  interimResults: boolean
  maxAlternatives: number
  onresult: ((event: SpeechRecognitionEvent) => void) | null
  onend: (() => void) | null
  onerror: (() => void) | null
  start(): void
  stop(): void
}

interface Window {
  SpeechRecognition?: { new (): SpeechRecognition }
  webkitSpeechRecognition?: { new (): SpeechRecognition }
}
