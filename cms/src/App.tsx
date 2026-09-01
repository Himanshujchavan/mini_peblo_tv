import { Navigate, NavLink, Route, Routes, useNavigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth";
import Login from "./pages/Login";
import ShowList from "./pages/ShowList";
import ShowEditor from "./pages/ShowEditor";
import Publish from "./pages/Publish";

function RequireAuth({ children }: { children: JSX.Element }) {
  const { email } = useAuth();
  if (!email) return <Navigate to="/login" replace />;
  return children;
}

function Shell() {
  const { email, role, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>Peblo TV CMS</h1>
        <nav>
          <NavLink to="/shows" className={({ isActive }) => (isActive ? "active" : "")}>Shows</NavLink>
          <NavLink to="/publish" className={({ isActive }) => (isActive ? "active" : "")}>Publish</NavLink>
          <button onClick={() => { logout(); navigate("/login"); }}>Sign out</button>
        </nav>
        {email && <p className="hint" style={{ marginTop: 20 }}>{email} · {role}</p>}
      </aside>
      <main className="main">
        <Routes>
          <Route path="/shows" element={<ShowList />} />
          <Route path="/shows/:showId" element={<ShowEditor />} />
          <Route path="/publish" element={<Publish />} />
          <Route path="*" element={<Navigate to="/shows" replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            <RequireAuth>
              <Shell />
            </RequireAuth>
          }
        />
      </Routes>
    </AuthProvider>
  );
}
