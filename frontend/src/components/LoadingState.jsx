export default function LoadingState() {
  return (
    <div className="animate-page-enter flex min-h-screen items-center justify-center bg-mist px-6">
      <div className="animate-glow-pulse flex items-center gap-3 rounded-2xl border border-slate-200 bg-white px-5 py-4 text-sm font-medium text-slate-600 shadow-sm">
        <span
          className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-electric"
          aria-hidden="true"
        />
        Checking your Jarvis session...
      </div>
    </div>
  );
}
