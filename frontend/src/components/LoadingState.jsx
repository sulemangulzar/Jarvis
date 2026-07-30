export default function LoadingState() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-mist px-6">
      <div className="flex items-center gap-3 text-sm font-medium text-slate-600">
        <span
          className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-electric"
          aria-hidden="true"
        />
        Checking your Jarvis session...
      </div>
    </div>
  );
}
