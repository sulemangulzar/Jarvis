import { getMicrosoftLoginUrl } from "../services/api";

export default function LoginButton({ disabled }) {
  function handleLogin() {
    // OAuth must use a browser navigation, not fetch().
    window.location.href = getMicrosoftLoginUrl();
  }

  return (
    <button
      type="button"
      onClick={handleLogin}
      disabled={disabled}
      className="inline-flex w-full items-center justify-center gap-3 rounded-xl bg-ink px-5 py-3.5 text-sm font-semibold text-white shadow-lg shadow-slate-900/10 transition hover:bg-slate-700 focus:outline-none focus:ring-4 focus:ring-blue-200 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
    >
      <span
        className="grid h-5 w-5 grid-cols-2 grid-rows-2 gap-0.5"
        aria-hidden="true"
      >
        <span className="bg-[#f25022]" />
        <span className="bg-[#7fba00]" />
        <span className="bg-[#00a4ef]" />
        <span className="bg-[#ffb900]" />
      </span>
      Sign in with Microsoft
    </button>
  );
}
