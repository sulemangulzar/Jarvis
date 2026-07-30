import { useEffect, useState } from "react";

import ChatWindow from "./ChatWindow";
import UserProfile from "./UserProfile";

const quickPrompts = [
  "Show my tasks",
  "What meetings do I have today?",
  "Show my latest emails",
  "Draft an email",
];

function JarvisMark() {
  return (
    <div className="grid h-10 w-10 grid-cols-2 grid-rows-2 gap-1 rounded-xl bg-ink p-2 dark:bg-slate-950 dark:shadow-[0_0_24px_rgba(34,211,238,0.35)]">
      <span className="rounded-sm bg-blue-400" />
      <span className="rounded-sm bg-cyan-300" />
      <span className="rounded-sm bg-indigo-300" />
      <span className="rounded-sm bg-white" />
    </div>
  );
}

function Sidebar() {
  return (
    <aside className="hidden min-h-screen w-64 shrink-0 flex-col border-r border-slate-200 bg-white px-5 py-6 dark:border-cyan-400/10 dark:bg-[#07111f] lg:flex">
      <div className="flex items-center gap-3 px-2">
        <JarvisMark />
        <span className="text-xl font-bold tracking-tight text-ink dark:text-white">Jarvis</span>
      </div>

      <nav className="mt-12 space-y-2" aria-label="Main navigation">
        <div className="flex items-center gap-3 rounded-xl bg-blue-50 px-3 py-3 text-sm font-semibold text-electric dark:bg-cyan-400/10 dark:text-cyan-300">
          <span aria-hidden="true">✦</span>
          Assistant
        </div>
        <div className="flex items-center gap-3 px-3 py-3 text-sm font-medium text-slate-500 dark:text-slate-400">
          <span aria-hidden="true">✓</span>
          To-Do
        </div>
        <div className="flex items-center gap-3 px-3 py-3 text-sm font-medium text-slate-500 dark:text-slate-400">
          <span aria-hidden="true">▣</span>
          Calendar
        </div>
        <div className="flex items-center gap-3 px-3 py-3 text-sm font-medium text-slate-500 dark:text-slate-400">
          <span aria-hidden="true">✉</span>
          Mail
        </div>
      </nav>

      <div className="mt-auto rounded-2xl bg-ink p-4 text-white dark:bg-gradient-to-br dark:from-cyan-400/20 dark:to-violet-500/20 dark:ring-1 dark:ring-cyan-300/20">
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-blue-300 dark:text-cyan-300">
          Jarvis tip
        </p>
        <p className="mt-2 text-sm leading-5 text-slate-200">
          Ask naturally. Jarvis can read, organize, and take action for you.
        </p>
      </div>
    </aside>
  );
}

export default function Dashboard({ user, onLogout, isLoggingOut }) {
  const [darkMode, setDarkMode] = useState(
    () => localStorage.getItem("jarvis-theme") === "dark",
  );

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
    localStorage.setItem("jarvis-theme", darkMode ? "dark" : "light");
  }, [darkMode]);

  return (
    <div className="min-h-screen bg-mist text-ink transition-colors dark:bg-[#030712] dark:text-slate-100 lg:flex lg:h-screen lg:overflow-hidden">
      <Sidebar />

      <main className="min-w-0 flex-1 lg:h-screen">
        <header className="border-b border-slate-200 bg-white px-5 py-5 dark:border-cyan-400/10 dark:bg-[#07111f] sm:px-8">
          <div className="mx-auto flex max-w-[1500px] items-center justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Personal workspace</p>
              <h1 className="mt-1 text-2xl font-bold tracking-tight text-ink dark:text-white sm:text-3xl">
                Good to see you, {user.display_name || "there"}.
              </h1>
            </div>
            <div className="flex items-center gap-2">
              <div className="hidden items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50 px-3 py-2 text-xs font-semibold text-emerald-700 dark:border-emerald-400/20 dark:bg-emerald-400/10 dark:text-emerald-300 sm:flex">
                <span className="h-2 w-2 rounded-full bg-emerald-500" aria-hidden="true" />
                Microsoft connected
              </div>
              <button
                type="button"
                onClick={() => setDarkMode((current) => !current)}
                aria-label={darkMode ? "Use light theme" : "Use dark theme"}
                className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-lg transition hover:border-cyan-300 hover:bg-cyan-50 focus:outline-none focus:ring-4 focus:ring-cyan-100 dark:border-cyan-400/20 dark:bg-slate-900 dark:hover:bg-cyan-400/10"
              >
                {darkMode ? "☀" : "☾"}
              </button>
            </div>
          </div>
        </header>

        <div className="mx-auto flex max-w-[1500px] flex-col gap-6 p-4 pb-6 sm:p-6 lg:h-[calc(100vh-89px)] lg:overflow-hidden lg:p-8 lg:pb-10">
          <section className="grid shrink-0 gap-4 sm:grid-cols-3">
            <div className="rounded-2xl border border-blue-100 bg-blue-50 p-5 dark:border-cyan-300/20 dark:bg-cyan-400/10 dark:shadow-[0_0_28px_rgba(34,211,238,0.08)]">
              <p className="text-sm font-medium text-blue-700 dark:text-cyan-300">Assistant</p>
              <p className="mt-2 text-lg font-bold text-ink dark:text-white">Ready to help</p>
              <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">Ask Jarvis anything</p>
            </div>
            <div className="rounded-2xl border border-violet-100 bg-violet-50 p-5 dark:border-violet-400/20 dark:bg-violet-400/10 dark:shadow-[0_0_28px_rgba(167,139,250,0.08)]">
              <p className="text-sm font-medium text-violet-700 dark:text-violet-300">Calendar</p>
              <p className="mt-2 text-lg font-bold text-ink dark:text-white">Stay organized</p>
              <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">View or create events</p>
            </div>
            <div className="rounded-2xl border border-amber-100 bg-amber-50 p-5 dark:border-amber-300/20 dark:bg-amber-400/10 dark:shadow-[0_0_28px_rgba(251,191,36,0.08)]">
              <p className="text-sm font-medium text-amber-700 dark:text-amber-300">To-Do</p>
              <p className="mt-2 text-lg font-bold text-ink dark:text-white">Keep moving</p>
              <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">Manage your tasks</p>
            </div>
          </section>

          <div className="grid min-h-0 flex-1 gap-6 xl:grid-cols-[minmax(0,1fr)_300px]">
            <ChatWindow suggestions={quickPrompts} />

            <aside className="space-y-6">
              <UserProfile user={user} onLogout={onLogout} isLoggingOut={isLoggingOut} />

              <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-cyan-400/10 dark:bg-[#0b1728]">
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-cyan-300">
                  Try asking
                </p>
                <div className="mt-4 space-y-2">
                  {quickPrompts.map((prompt) => (
                    <div
                      key={prompt}
                      className="rounded-xl bg-mist px-3 py-2.5 text-sm text-slate-600 dark:bg-slate-900 dark:text-slate-300"
                    >
                      {prompt}
                    </div>
                  ))}
                </div>
              </section>
            </aside>
          </div>
        </div>
      </main>
    </div>
  );
}
