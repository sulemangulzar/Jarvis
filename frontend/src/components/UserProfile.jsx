export default function UserProfile({ user, onLogout, isLoggingOut }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card dark:border-cyan-400/10 dark:bg-[#0b1728] dark:shadow-[0_0_32px_rgba(34,211,238,0.08)] sm:p-8">
      <div className="flex items-start justify-between gap-5">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.2em] text-electric">
            Active session
          </p>
          <h2 className="mt-3 text-2xl font-bold tracking-tight text-ink dark:text-white">
            Welcome, {user.display_name || "there"}.
          </h2>
        </div>
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-electric dark:bg-cyan-400/10 dark:text-cyan-300">
          {(user.display_name || user.email || "J").charAt(0).toUpperCase()}
        </div>
      </div>

      <div className="mt-8 rounded-xl bg-mist p-4 dark:bg-slate-900">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
          Email
        </p>
        <p className="mt-1 break-all text-sm font-medium text-slate-800 dark:text-slate-200">
          {user.email || "No email returned by Microsoft"}
        </p>
      </div>

      <button
        type="button"
        onClick={onLogout}
        disabled={isLoggingOut}
        className="mt-6 w-full rounded-xl border border-slate-300 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-slate-200 disabled:cursor-not-allowed disabled:opacity-60 dark:border-cyan-400/15 dark:text-slate-300 dark:hover:border-cyan-300 dark:hover:bg-cyan-400/10 dark:focus:ring-cyan-400/10"
      >
        {isLoggingOut ? "Signing out..." : "Sign out"}
      </button>
    </section>
  );
}
