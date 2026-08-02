import { useEffect, useRef, useState } from "react";

import { sendChatMessage } from "../services/api";

function renderInlineMarkdown(text) {
  const parts = text.split(/(\*\*.*?\*\*|\[.*?\]\(https?:\/\/.*?\))/g);

  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={index} className="font-bold text-ink dark:text-white">
          {part.slice(2, -2)}
        </strong>
      );
    }

    const link = part.match(/^\[(.*?)\]\((https?:\/\/.*?)\)$/);
    if (link) {
      return (
        <a
          key={index}
          href={link[2]}
          target="_blank"
          rel="noreferrer"
          className="mx-1 inline-flex items-center rounded-lg bg-blue-50 px-2.5 py-1 text-xs font-semibold text-electric underline decoration-blue-200 underline-offset-2 transition hover:bg-blue-100 dark:bg-cyan-400/10 dark:text-cyan-300 dark:decoration-cyan-400/30 dark:hover:bg-cyan-400/20"
        >
          {link[1]} ↗
        </a>
      );
    }

    return <span key={index}>{part}</span>;
  });
}

function renderAssistantContent(content) {
  const outlookLink = content.match(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/);
  const isCalendarMessage =
    /calendar event|calendar|event created|meeting (has been )?created/i.test(
      content,
    ) && outlookLink;
  const lines = content.split("\n").filter((line) => line.trim());
  const emailItems = [];
  let currentEmail = null;

  for (const line of lines) {
    const cleanLine = line.replace(/\*\*/g, "").trim();
    const subject = cleanLine.match(/^\d+\.\s*Subject:\s*(.+)$/i);
    if (subject) {
      if (currentEmail) emailItems.push(currentEmail);
      currentEmail = { subject: subject[1] };
      continue;
    }
    if (!currentEmail) continue;

    const field = cleanLine.match(/^(From|Received|Preview|Status):\s*(.+)$/i);
    if (field) {
      currentEmail[field[1].toLowerCase()] = field[2];
    }
  }
  if (currentEmail) emailItems.push(currentEmail);

  const taskLines = lines
    .map((line) =>
      line.match(/^\s*\d+\.\s+\*\*(.+?)\*\*\s+-\s+Status:\s*(.+)$/i),
    )
    .filter(Boolean);
  const numberedItems = lines
    .map((line) =>
      line.match(/^\s*\d+\.\s+\*\*(.+?)\*\*(?:\s+-\s+(.+))?$/),
    )
    .filter(Boolean);

  if (isCalendarMessage) {
    const messageWithoutLink = content.replace(outlookLink[0], "").trim();
    return (
      <div className="space-y-3 break-words">
        <p>{renderInlineMarkdown(messageWithoutLink)}</p>
        <a
          href={outlookLink[2]}
          target="_blank"
          rel="noreferrer"
          className="flex items-center justify-between rounded-xl border border-violet-200 bg-violet-50 px-4 py-3 text-sm font-semibold text-violet-700 transition hover:bg-violet-100 dark:border-violet-400/20 dark:bg-violet-400/10 dark:text-violet-300 dark:hover:bg-violet-400/20"
        >
          <span>Open in Outlook Calendar</span>
          <span aria-hidden="true">↗</span>
        </a>
      </div>
    );
  }

  if (emailItems.length > 0) {
    return (
      <div className="space-y-3">
        <p className="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300">
          Your latest emails
        </p>
        {emailItems.map((email, index) => (
          <article
            key={`${email.subject}-${index}`}
            className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-cyan-400/10 dark:bg-slate-900"
          >
            <div className="flex items-start justify-between gap-3">
              <h3 className="min-w-0 break-words text-sm font-bold text-ink dark:text-white">
                {email.subject}
              </h3>
              {email.status && (
                <span
                  className={`shrink-0 rounded-full px-2 py-1 text-[11px] font-bold ${
                    email.status.toLowerCase().includes("unread")
                      ? "bg-amber-100 text-amber-700 dark:bg-amber-400/10 dark:text-amber-300"
                      : "bg-emerald-100 text-emerald-700 dark:bg-emerald-400/10 dark:text-emerald-300"
                  }`}
                >
                  {email.status}
                </span>
              )}
            </div>
            <div className="mt-3 space-y-1 text-xs leading-5 text-slate-500 dark:text-slate-400">
              {email.from && <p><strong>From:</strong> {email.from}</p>}
              {email.received && <p><strong>Received:</strong> {email.received}</p>}
              {email.preview && <p className="break-words"><strong>Preview:</strong> {email.preview}</p>}
            </div>
          </article>
        ))}
      </div>
    );
  }

  if (taskLines.length > 0) {
    return (
      <div className="space-y-2">
        <p className="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300">
          Your Microsoft To-Do tasks
        </p>
        {taskLines.map((match, index) => (
          <div
            key={`${match[1]}-${index}`}
            className="flex items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white px-3 py-3 shadow-sm dark:border-cyan-400/10 dark:bg-slate-900"
          >
            <div className="flex min-w-0 items-center gap-3">
              <span
                className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-blue-100 text-sm text-electric dark:bg-cyan-400/10 dark:text-cyan-300"
                aria-hidden="true"
              >
                ✓
              </span>
              <span className="truncate text-sm font-semibold text-ink dark:text-white">
                {match[1]}
              </span>
            </div>
            <span className="shrink-0 rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600 dark:bg-cyan-400/10 dark:text-cyan-300">
              {match[2]}
            </span>
          </div>
        ))}
      </div>
    );
  }

  if (numberedItems.length > 0) {
    return (
      <div className="space-y-2">
        {numberedItems.map((match, index) => (
          <div
            key={`${match[1]}-${index}`}
            className="rounded-xl border border-slate-200 bg-white px-4 py-3 shadow-sm dark:border-cyan-400/10 dark:bg-slate-900"
          >
            <p className="text-sm font-semibold text-ink dark:text-white">
              {match[1]}
            </p>
            {match[2] && (
              <p className="mt-1 break-words text-xs leading-5 text-slate-500 dark:text-slate-400">
                {renderInlineMarkdown(match[2])}
              </p>
            )}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-2 whitespace-pre-wrap break-words">
      {lines.map((line, index) => (
        <p key={index}>{renderInlineMarkdown(line)}</p>
      ))}
    </div>
  );
}

function Message({ role, content }) {
  const isUser = role === "user";

  return (
    <div className={`animate-message-in flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[92%] rounded-2xl px-4 py-3 text-sm leading-6 ${
          isUser
            ? "rounded-br-sm bg-ink text-white dark:bg-gradient-to-r dark:from-cyan-500 dark:to-violet-500"
            : "rounded-bl-sm border border-slate-200 bg-white text-slate-700 shadow-sm dark:border-cyan-400/10 dark:bg-[#0b1728] dark:text-slate-200"
        }`}
      >
        {isUser ? content : renderAssistantContent(content)}
      </div>
    </div>
  );
}

export default function ChatWindow({ suggestions = [] }) {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello. I can help you read email, create drafts, manage calendar events, and manage Microsoft To-Do tasks.",
    },
  ]);
  const [message, setMessage] = useState("");
  const [conversationId, setConversationId] = useState(null);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  async function handleSubmit(event) {
    event.preventDefault();
    const trimmedMessage = message.trim();
    if (!trimmedMessage || isSending) return;

    setError(null);
    setMessage("");
    setMessages((current) => [
      ...current,
      { role: "user", content: trimmedMessage },
    ]);
    setIsSending(true);

    try {
      const result = await sendChatMessage(trimmedMessage, conversationId);
      setConversationId(result.conversation_id);
      setMessages((current) => [
        ...current,
        { role: "assistant", content: result.message },
      ]);
    } catch (requestError) {
      setError(
        requestError.message || "Jarvis could not answer. Please try again.",
      );
    } finally {
      setIsSending(false);
    }
  }

  function handleInputKeyDown(event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  return (
    <section className="flex min-h-[560px] flex-1 flex-col rounded-2xl border border-slate-200 bg-white shadow-card dark:border-cyan-400/15 dark:bg-[#0b1728] dark:shadow-[0_0_45px_rgba(34,211,235,0.08)] xl:h-full">
      <div className="border-b border-slate-100 px-5 py-4 dark:border-cyan-400/10 sm:px-6">
        <p className="text-xs font-bold uppercase tracking-[0.2em] text-electric">
          Jarvis assistant
        </p>
        <h2 className="mt-1 text-lg font-bold text-ink dark:text-white">
          What can I help with?
        </h2>
      </div>

      <div
        className="flex flex-1 flex-col gap-3 overflow-y-auto px-5 py-5 sm:px-6"
        aria-live="polite"
      >
        {messages.map((item, index) => (
          <Message key={`${item.role}-${index}`} {...item} />
        ))}
        <div ref={messagesEndRef} />
        {isSending && (
          <div className="flex items-center gap-2 text-sm text-slate-500 dark:text-cyan-300">
            <span
              className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-slate-300 border-t-electric"
              aria-hidden="true"
            />
            <span className="inline-flex items-center gap-1">
              Jarvis is thinking
              <span className="flex gap-0.5" aria-hidden="true">
                <span className="animate-dot-bounce h-1.5 w-1.5 rounded-full bg-electric" />
                <span className="animate-dot-bounce h-1.5 w-1.5 rounded-full bg-electric [animation-delay:150ms]" />
                <span className="animate-dot-bounce h-1.5 w-1.5 rounded-full bg-electric [animation-delay:300ms]" />
              </span>
            </span>
          </div>
        )}
      </div>

      {error && (
        <div
          role="alert"
          className="mx-5 mb-3 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-400/20 dark:bg-red-400/10 dark:text-red-300 sm:mx-6"
        >
          {error}
        </div>
      )}

      {suggestions.length > 0 && messages.length === 1 && (
        <div className="border-t border-slate-100 px-5 py-4 dark:border-cyan-400/10 sm:px-6">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-400 dark:text-slate-500">
            Quick prompts
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                onClick={() => setMessage(suggestion)}
                className="rounded-full border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:border-blue-300 hover:bg-blue-50 hover:text-electric focus:outline-none focus:ring-4 focus:ring-blue-100 dark:border-cyan-400/15 dark:text-slate-300 dark:hover:bg-cyan-400/10 dark:hover:text-cyan-300"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="animate-glow-pulse border-t border-slate-100 p-4 dark:border-cyan-400/10 sm:p-5"
      >
        <label htmlFor="chat-message" className="sr-only">
          Message Jarvis
        </label>
        <div className="flex gap-2">
          <textarea
            id="chat-message"
            rows="1"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            onKeyDown={handleInputKeyDown}
            placeholder="Ask about your calendar, email, or tasks..."
            disabled={isSending}
            className="min-h-[48px] min-w-0 flex-1 resize-y rounded-xl border border-slate-300 px-4 py-3 text-sm text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-electric focus:ring-4 focus:ring-blue-100 disabled:bg-slate-50 dark:border-cyan-400/15 dark:bg-slate-900 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:border-cyan-300 dark:focus:ring-cyan-400/10 dark:disabled:bg-slate-950"
          />
          <button
            type="submit"
            disabled={isSending || !message.trim()}
            className="rounded-xl bg-electric px-4 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 focus:outline-none focus:ring-4 focus:ring-blue-200 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-gradient-to-r dark:from-cyan-500 dark:to-violet-500 dark:hover:from-cyan-400 dark:hover:to-violet-400"
          >
            Send
          </button>
        </div>
      </form>
    </section>
  );
}
