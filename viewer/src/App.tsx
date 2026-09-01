import { Routes, Route } from "react-router-dom";
import NavBar from "./components/NavBar";
import Home from "./pages/Home";
import Search from "./pages/Search";
import ShowDetail from "./pages/ShowDetail";

export default function App() {
  return (
    <div className="app-shell">
      <div className="container">
        <NavBar />
      </div>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/search" element={<Search />} />
        <Route path="/shows/:showId" element={<ShowDetail />} />
      </Routes>
    </div>
  );
}
