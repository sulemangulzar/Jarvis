import { useEffect, useState } from "react";

import Dashboard from "./components/Dashboard";
import LoadingState from "./components/LoadingState";
import LoginButton from "./components/LoginButton";
import { getAuthStatus, logout } from "./services/api";

function App() {
  const [authState, setAuthState] = useState({
    loading: true,
    authenticated: false,
    user: null,
    error: null,
  });
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function checkSession() {
      try {
        const result = await getAuthStatus();
        if (isMounted) {
          setAuthState({
            loading: false,
            authenticated: result.authenticated,
            user: result.user,
            error: null,
          });
        }
      } catch {
        if (isMounted) {
          setAuthState({
            loading: false,
            authenticated: false,
            user: null,
            error: "We could not connect to Jarvis. Is the backend running?",
          });
        }
      }
    }

    checkSession();

    return () => {
      isMounted = false;
    };
  }, []);

  async function handleLogout() {
    setIsLoggingOut(true);
    try {
      await logout();
      setAuthState({
        loading: false,
        authenticated: false,
        user: null,
        error: null,
      });
    } catch {
      setAuthState((current) => ({
        ...current,
        error: "We could not sign you out. Please try again.",
      }));
    } finally {
      setIsLoggingOut(false);
    }
  }

  if (authState.loading) {
    return <LoadingState />;
  }

  if (authState.authenticated) {
    return (
      <Dashboard
        user={authState.user}
        onLogout={handleLogout}
        isLoggingOut={isLoggingOut}
      />
    );
  }

  return (
    <main className="min-h-screen bg-mist px-6 py-10 text-ink sm:py-16">
      <div className="mx-auto flex min-h-[80vh] w-full max-w-5xl items-center justify-center">
        <div className="grid w-full gap-10 lg:grid-cols-[1.05fr_0.95fr] lg:items-center">
          <section className="max-w-xl">
            <div className="mb-8 flex items-center gap-3">
              <div className="grid h-11 w-11 grid-cols-2 grid-rows-2 gap-1 rounded-xl bg-ink p-2 shadow-lg shadow-slate-900/10">
                <span className="rounded-sm bg-blue-400" />
                <span className="rounded-sm bg-cyan-300" />
                <span className="rounded-sm bg-indigo-300" />
                <span className="rounded-sm bg-white" />
              </div>
              <span className="text-xl font-bold tracking-tight">Jarvis</span>
            </div>

            <p className="text-sm font-bold uppercase tracking-[0.24em] text-electric">
              Your personal workspace
            </p>
            <h1 className="mt-5 text-4xl font-bold leading-tight tracking-tight text-ink sm:text-6xl">
              A calmer way to get things done.
            </h1>
            <p className="mt-6 max-w-lg text-base leading-7 text-slate-600 sm:text-lg">
              Sign in securely with your Microsoft account to continue to your
              Jarvis workspace.
            </p>
          </section>

          <section className="w-full max-w-md justify-self-center lg:justify-self-end">
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-card sm:p-8">
                <p className="text-xs font-bold uppercase tracking-[0.2em] text-slate-500">
                  Get started
                </p>
                <h2 className="mt-3 text-2xl font-bold tracking-tight text-ink">
                  Sign in to Jarvis
                </h2>
                <p className="mt-3 text-sm leading-6 text-slate-600">
                  Your Microsoft account will be used only to verify your
                  identity.
                </p>

                {authState.error && (
                  <div
                    role="alert"
                    className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm leading-5 text-red-700"
                  >
                    {authState.error}
                  </div>
                )}

                <div className="mt-7">
                  <LoginButton disabled={false} />
                </div>
              </div>
          </section>
        </div>
      </div>
    </main>
  );
}

export default App;
