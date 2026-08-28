import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Send, Sparkles, Bot, User as UserIcon } from 'lucide-react'
import { api } from '@/lib/api'
import { Card } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Field'
import { Badge } from '@/components/ui/Badge'
import type { ChatMessage } from '@/lib/types'

export default function AIAssistant() {
  const { t, i18n } = useTranslation()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [source, setSource] = useState<'llm' | 'rule_based' | null>(null)
  const [prompts, setPrompts] = useState<string[]>([])
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    api.get('/api/chat/history').then(({ data }) => setMessages(data)).catch(() => {})
    api.get(`/api/chat/prompts?language=${i18n.language}`).then(({ data }) => setPrompts(data.prompts)).catch(() => {})
  }, [i18n.language])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function send(text?: string) {
    const message = (text ?? input).trim()
    if (!message || sending) return
    setInput('')
    setSending(true)
    setMessages((prev) => [...prev, { role: 'user', content: message, created_at: new Date().toISOString() }])
    try {
      const { data } = await api.post('/api/chat', { message, language: i18n.language })
      setSource(data.source)
      setMessages((prev) => [...prev, { role: 'assistant', content: data.reply, created_at: new Date().toISOString() }])
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: t('common.error_generic'), created_at: new Date().toISOString() },
      ])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="flex h-[calc(100vh-8.5rem)] flex-col">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">{t('chat.title')}</h1>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">{t('chat.subtitle')}</p>
        </div>
        {source && (
          <Badge tone={source === 'llm' ? 'ai' : 'neutral'}>
            {source === 'llm' ? t('chat.source_llm') : t('chat.source_rule_based')}
          </Badge>
        )}
      </div>

      <Card className="flex flex-1 flex-col overflow-hidden">
        <div className="flex-1 space-y-4 overflow-y-auto p-5">
          {messages.length === 0 && (
            <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
              <div className="ai-glow flex h-12 w-12 items-center justify-center rounded-2xl bg-ai-100 text-ai-400">
                <Bot size={24} aria-hidden="true" />
              </div>
              <p className="text-sm text-[var(--text-secondary)]">{t('chat.subtitle')}</p>
            </div>
          )}

          {messages.map((m, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex items-start gap-2.5 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              <div
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                  m.role === 'user' ? 'bg-brand-500 text-brand-900' : 'bg-ai-100 text-ai-400'
                }`}
              >
                {m.role === 'user' ? <UserIcon size={14} aria-hidden="true" /> : <Bot size={14} aria-hidden="true" />}
              </div>
              <div
                className={`max-w-[75%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm ${
                  m.role === 'user'
                    ? 'bg-brand-500 text-brand-900'
                    : 'border border-ai-300/30 bg-[var(--bg-surface-muted)] text-[var(--text-primary)]'
                }`}
              >
                {m.content}
              </div>
            </motion.div>
          ))}

          {sending && (
            <div className="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-ai-400 [animation-delay:-0.2s]" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-ai-400" />
              <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-ai-400 [animation-delay:0.2s]" />
              {t('chat.thinking')}
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {messages.length === 0 && prompts.length > 0 && (
          <div className="flex flex-wrap gap-2 border-t border-[var(--border-subtle)] px-5 py-3">
            {prompts.map((p) => (
              <button
                key={p}
                onClick={() => send(p)}
                className="rounded-full border border-[var(--border-subtle)] px-3 py-1.5 text-xs text-[var(--text-secondary)] hover:bg-[var(--bg-surface-muted)]"
              >
                <Sparkles size={11} className="mr-1 inline text-ai-400" aria-hidden="true" />
                {p}
              </button>
            ))}
          </div>
        )}

        <form
          onSubmit={(e) => {
            e.preventDefault()
            send()
          }}
          className="flex items-center gap-2 border-t border-[var(--border-subtle)] p-3"
        >
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={t('chat.placeholder')}
            disabled={sending}
          />
          <Button type="submit" disabled={!input.trim()} isLoading={sending}>
            <Send size={15} aria-hidden="true" />
          </Button>
        </form>
      </Card>
    </div>
  )
}
