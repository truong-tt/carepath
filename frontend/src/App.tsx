import { useState } from "react";

import "./App.css";
import { createSession } from "./api";
import { AdminReview } from "./components/AdminReview";
import { ConsentGate, type ConsentPayload } from "./components/ConsentGate";
import { InterpreterConsole } from "./components/InterpreterConsole";

function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  if (window.location.pathname === "/admin") {
    return <AdminReview />;
  }

  async function handleConsent(consent: ConsentPayload) {
    setStarting(true);
    setError(null);
    try {
      const result = await createSession({ consent });
      setSessionId(result.session_id);
    } catch {
      setError("Could not start the session. Check that the backend is running.");
    } finally {
      setStarting(false);
    }
  }

  if (sessionId) {
    return <InterpreterConsole sessionId={sessionId} />;
  }

  return <ConsentGate error={error} isSubmitting={starting} onConsent={handleConsent} />;
}

export default App;
