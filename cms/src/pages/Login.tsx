import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

export default function Login() {
  const { login, loading } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("editor@peblo.tv");
  const [password, setPassword] = useState("editor123");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await login(email, password);
      navigate("/shows");
    } catch (err: any) {
      setError(err.message || "Couldn't sign in — check your email and password.");
    }
  }

  return (
    <div className="login-wrap">
      <form className="login-card" onSubmit={submit}>
        <h1>Peblo TV — CMS</h1>
        <p className="page-sub">Sign in to manage shows and episodes.</p>
        {error && <div className="callout callout-error">{error}</div>}
        <div className="form-field" style={{ marginBottom: 12 }}>
          <label>Email</label>
          <input className="input" value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
        </div>
        <div className="form-field" style={{ marginBottom: 16 }}>
          <label>Password</label>
          <input className="input" value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />
        </div>
        <button className="btn btn-primary" style={{ width: "100%" }} disabled={loading}>
          {loading ? "Signing in..." : "Sign in"}
        </button>
        <p className="page-sub" style={{ marginTop: 14, fontSize: 12 }}>
          Demo accounts: editor@peblo.tv / editor123 (editor) — admin@peblo.tv / admin123 (admin, can publish)
        </p>
      </form>
    </div>
  );
}
