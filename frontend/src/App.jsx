// Rutas, layout con menú y protección por sesión/rol.
import { Navigate, NavLink, Outlet, Route, Routes, useNavigate } from "react-router-dom";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Empleados from "./pages/Empleados.jsx";
import Puestos from "./pages/Puestos.jsx";
import Evaluaciones from "./pages/Evaluaciones.jsx";
import Desarrollo from "./pages/Desarrollo.jsx";
import Contribuciones from "./pages/Contribuciones.jsx";

const rol = () => localStorage.getItem("rol");
const logged = () => !!localStorage.getItem("token");

// Menú: qué roles ven cada sección (el backend igualmente valida)
const MENU = [
  { to: "/", label: "Dashboard", roles: ["admin", "rrhh"] },
  { to: "/empleados", label: "Empleados", roles: ["admin", "rrhh", "evaluador", "responsable_area"] },
  { to: "/puestos", label: "Puestos", roles: ["admin", "rrhh", "evaluador", "responsable_area"] },
  { to: "/evaluaciones", label: "Evaluaciones", roles: ["admin", "rrhh", "evaluador"] },
  { to: "/desarrollo", label: "Desarrollo", roles: ["admin", "rrhh", "evaluador", "responsable_area"] },
  { to: "/contribuciones", label: "Contribuciones", roles: ["admin", "rrhh", "responsable_area"] },
];

function Layout() {
  const nav = useNavigate();
  if (!logged()) return <Navigate to="/login" replace />;
  const items = MENU.filter((m) => m.roles.includes(rol()));
  return (
    <div className="shell">
      <aside>
        <h1>RRHH</h1>
        {items.map((m) => (
          <NavLink key={m.to} to={m.to} end={m.to === "/"}>{m.label}</NavLink>
        ))}
        <div className="spacer" />
        <small>{localStorage.getItem("email")} · {rol()}</small>
        <button className="ghost" onClick={() => { localStorage.clear(); nav("/login"); }}>Cerrar sesión</button>
      </aside>
      <main><Outlet /></main>
    </div>
  );
}

export default function App() {
  const home = rol() === "admin" || rol() === "rrhh" ? <Dashboard /> : <Navigate to="/empleados" replace />;
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<Layout />}>
        <Route index element={home} />
        <Route path="empleados" element={<Empleados />} />
        <Route path="puestos" element={<Puestos />} />
        <Route path="evaluaciones" element={<Evaluaciones />} />
        <Route path="desarrollo" element={<Desarrollo />} />
        <Route path="contribuciones" element={<Contribuciones />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
