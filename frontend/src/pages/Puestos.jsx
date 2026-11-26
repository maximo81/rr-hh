// CU2: puestos de trabajo con sus requisitos (habilidades, conocimientos, especificación) y sus posiciones.
import { useEffect, useRef, useState } from "react";
import api from "../api";

const CATEGORIAS = [["directivo", "Directivo"], ["jefatura", "Jefatura"], ["tecnico", "Técnico"], ["operativo", "Operativo"]];
const ESTADOS_EDITABLES = [["vacante", "Vacante"], ["congelada", "Congelada"]]; // "ocupada" solo se ve
const ESTADOS = { vacante: "Vacante", congelada: "Congelada", ocupada: "Ocupada" };
const AYUDA_OCUPANTE = "Para asignar un ocupante, ve a Empleados, pulsa \"Modificar\" en la persona y elige este puesto. "
  + "Se usará una posición vacante del puesto (o se creará una nueva).";
const VACIO = { codigo: "", titulo: "", unidad: "", mision: "", categoria: "", educacion: "", experiencia: "", habilidades: [], conocimientos: [], posiciones: [] };
const ESPERA_CODIGO = 2000; // ms sin escribir antes de verificar el código

const codigoEnUso = async (codigo, excluir) =>
  !(await api.get("/puestos/codigo-disponible", { params: { codigo: codigo.trim(), excluir } })).data.disponible;

// Detalle del backend (GET /puestos/{id}) -> estado del formulario
function desdeDetalle(d) {
  const esp = d.especificaciones[0] || {};
  return {
    codigo: d.codigo, titulo: d.titulo, unidad: String(d.departamentos_id_dpto), mision: d.mision || "",
    categoria: esp.categoria || "", educacion: esp.especificacion_puestocol || "", experiencia: esp.experiencia_necesaria || "",
    habilidades: d.habilidades.map((h) => h.id_habilidad), conocimientos: d.conocimientos.map((k) => k.id_conocimiento),
    posiciones: d.posiciones.map((p) => ({ id_posicion: p.id_posicion, localizacion: p.localizacion_fisica || "", estado: p.estado, ocupante: p.ocupante })),
  };
}

function validar(f) {
  const e = {};
  if (!f.codigo.trim()) e.codigo = "Obligatorio"; else if (f.codigo.length > 20) e.codigo = "Máximo 20 caracteres";
  if (!f.titulo.trim()) e.titulo = "Obligatorio"; else if (f.titulo.length > 80) e.titulo = "Máximo 80 caracteres";
  if (!f.unidad) e.unidad = "Obligatorio";
  if (!f.categoria) e.categoria = "Obligatorio";
  if (f.educacion.length > 80) e.educacion = "Máximo 80 caracteres";
  return e;
}

function Casillas({ items, idKey, marcados, onToggle, disabled }) {
  return (
    <div className="checks">
      {items.map((it) => (
        <label key={it[idKey]}>
          <input type="checkbox" checked={marcados.includes(it[idKey])} onChange={() => onToggle(it[idKey])} disabled={disabled} />{it.descripcion}
        </label>
      ))}
    </div>
  );
}

// Segundo modal: cupos del puesto. No se cierra con click afuera; "Aceptar" solo actualiza el formulario,
// todo se guarda junto con el puesto. Las posiciones ocupadas (o todas, con soloLectura) se muestran sin editar.
function Posiciones({ titulo, inicial, soloLectura, onAceptar, onCancel }) {
  const [rows, setRows] = useState(inicial);
  const setRow = (i, k) => (e) => setRows(rows.map((r, j) => (j === i ? { ...r, [k]: e.target.value } : r)));
  const quitar = (i) => setRows(rows.filter((_, j) => j !== i));
  const agregar = () => setRows([...rows, { localizacion: "", estado: "vacante" }]);
  return (
    <div className="modal-bg">
      <div className="card modal ancho">
        <div className="modal-cab"><b>Posiciones · {titulo}</b></div>
        {rows.length === 0 ? <p className="vacio">Este puesto todavía no tiene posiciones.</p> : (
          <table>
            <thead><tr><th>Localización física</th><th>Estado</th><th>Ocupante<span className="ayuda" tabIndex={0} aria-label={AYUDA_OCUPANTE} data-tip={AYUDA_OCUPANTE}>?</span></th><th></th></tr></thead>
            <tbody>{rows.map((r, i) => soloLectura || r.estado === "ocupada" ? (
              <tr key={i}><td>{r.localizacion || "—"}</td><td>{ESTADOS[r.estado]}</td><td>{r.ocupante || "—"}</td><td></td></tr>
            ) : (
              <tr key={i}>
                <td><input value={r.localizacion} onChange={setRow(i, "localizacion")} maxLength={80} placeholder="Opcional" /></td>
                <td><select value={r.estado} onChange={setRow(i, "estado")}>
                  {ESTADOS_EDITABLES.map(([v, t]) => <option key={v} value={v}>{t}</option>)}</select></td>
                <td>—</td>
                <td><button type="button" className="sec" title="Quitar posición" onClick={() => quitar(i)}>✕</button></td>
              </tr>))}
            </tbody>
          </table>
        )}
        {soloLectura ? (
          <div className="acciones"><button type="button" className="sec" onClick={onCancel}>Cerrar</button></div>
        ) : (<>
          <div><button type="button" className="sec" onClick={agregar}>+ Agregar posición</button></div>
          <div className="acciones">
            {/* Limpiar quita las posiciones editables; las ocupadas no se pueden quitar desde aquí */}
            <button type="button" className="sec" style={{ marginRight: "auto" }}
              onClick={() => setRows(rows.filter((r) => r.estado === "ocupada"))}>Limpiar</button>
            <button type="button" className="sec" onClick={onCancel}>Cancelar</button>
            <button type="button" onClick={() => onAceptar(rows)}>Aceptar</button>
          </div>
        </>)}
      </div>
    </div>
  );
}

// Modal de alta (idPuesto = null), modificación o consulta (soloLectura: todo bloqueado, solo "Cerrar").
// onClose(borrador): con click afuera devuelve lo cargado para retomarlo al reabrir; con Cancelar, null.
function PuestoForm({ idPuesto, inicial, soloLectura, departamentos, habilidades, conocimientos, onClose, onGuardado }) {
  const [f, setF] = useState(inicial?.f ?? VACIO);
  const [codigoEstado, setCodigoEstado] = useState(inicial?.codigoEstado ?? "idle"); // idle | pendiente | verificando | ok | ocupado
  const [intentado, setIntentado] = useState(inicial?.intentado ?? false);
  const [error, setError] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [verPosiciones, setVerPosiciones] = useState(false);
  const timer = useRef(null);
  useEffect(() => () => clearTimeout(timer.current), []);

  const set = (k) => (e) => { setF({ ...f, [k]: e.target.value }); setError(""); };
  const toggle = (k) => (id) => setF({ ...f, [k]: f[k].includes(id) ? f[k].filter((x) => x !== id) : [...f[k], id] });

  async function verificarCodigo(valor) {
    clearTimeout(timer.current);
    if (!valor.trim()) { setCodigoEstado("idle"); return "idle"; }
    setCodigoEstado("verificando");
    let estado;
    try { estado = (await codigoEnUso(valor, idPuesto ?? undefined)) ? "ocupado" : "ok"; }
    catch { estado = "idle"; } // si falla la consulta, el backend igual rechaza un código repetido al guardar
    setCodigoEstado(estado);
    return estado;
  }

  function onCodigo(e) {
    const v = e.target.value;
    setF({ ...f, codigo: v }); setError("");
    clearTimeout(timer.current);
    if (!v.trim()) return setCodigoEstado("idle");
    setCodigoEstado("pendiente");
    timer.current = setTimeout(() => verificarCodigo(v), ESPERA_CODIGO);
  }

  async function guardar(e) {
    e.preventDefault(); setIntentado(true); setError("");
    // Si el usuario guarda antes de los 2 s (o el código no se verificó), se verifica primero
    const sinVerificar = codigoEstado === "pendiente" || (codigoEstado === "idle" && f.codigo.trim());
    const estado = sinVerificar ? await verificarCodigo(f.codigo) : codigoEstado;
    if (Object.keys(validar(f)).length > 0 || estado === "ocupado") return;
    const body = {
      codigo: f.codigo, titulo: f.titulo, mision: f.mision || null, departamentos_id_dpto: Number(f.unidad),
      categoria: f.categoria, educacion: f.educacion || null, experiencia: f.experiencia || null,
      habilidades: f.habilidades, conocimientos: f.conocimientos,
      // Las ocupadas no se envían: se gestionan desde Empleados
      posiciones: f.posiciones.filter((p) => p.estado !== "ocupada")
        .map((p) => ({ id_posicion: p.id_posicion ?? null, localizacion_fisica: p.localizacion || null, estado: p.estado })),
    };
    setGuardando(true);
    try {
      if (idPuesto) await api.put(`/puestos/${idPuesto}`, body);
      else await api.post("/puestos", body);
      onGuardado(idPuesto ? "Puesto actualizado" : "Puesto creado");
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Error al guardar");
      setGuardando(false);
    }
  }

  const errs = intentado ? validar(f) : {};
  if (codigoEstado === "ocupado") errs.codigo = "El código ya está en uso";
  const verificando = codigoEstado === "verificando";
  const ro = !!soloLectura;
  const claseCodigo = errs.codigo ? "input-err" : codigoEstado === "ok" ? "input-ok" : "";
  const err = (k) => errs[k] && <small className="err">{errs[k]}</small>;

  function limpiar() { // las posiciones ocupadas se mantienen (no se pueden quitar desde aquí)
    clearTimeout(timer.current);
    setF({ ...VACIO, posiciones: f.posiciones.filter((p) => p.estado === "ocupada") });
    setCodigoEstado("idle"); setIntentado(false); setError("");
  }
  // Una verificación a medio hacer no se conserva: al reabrir se vuelve a verificar al guardar
  const cerrarAfuera = () => onClose({ f, intentado,
    codigoEstado: ["pendiente", "verificando"].includes(codigoEstado) ? "idle" : codigoEstado });

  const tituloPuesto = [f.codigo.trim(), f.titulo.trim()].filter(Boolean).join(" · ") || "Nuevo puesto";

  return (<>
    {/* Cierra al hacer click en el fondo (mousedown: no cierra si se arrastra una selección desde adentro) */}
    <div className="modal-bg" onMouseDown={(e) => e.target === e.currentTarget && cerrarAfuera()}>
      <form className="card modal ancho" onSubmit={guardar} noValidate>
        <div className="modal-cab">
          <b>{ro ? "Ver puesto" : idPuesto ? "Modificar puesto" : "Nuevo puesto"}</b>
          <button type="button" className="sec" onClick={() => setVerPosiciones(true)}>Posiciones ({f.posiciones.length})</button>
        </div>

        <div className="seccion">Datos del puesto</div>
        <div className="form">
          <div><label>Código</label>
            <div className="con-spinner">
              <input value={f.codigo} onChange={onCodigo} disabled={ro || verificando} className={claseCodigo} maxLength={20} autoFocus={!ro} />
              {verificando && <span className="spinner" />}
            </div>{err("codigo")}</div>
          <div><label>Título</label><input value={f.titulo} onChange={set("titulo")} disabled={ro} className={errs.titulo ? "input-err" : ""} maxLength={80} />{err("titulo")}</div>
          <div><label>Unidad</label>
            <select value={f.unidad} onChange={set("unidad")} disabled={ro} className={errs.unidad ? "input-err" : ""}><option value="">Seleccionar…</option>
              {departamentos.map((d) => <option key={d.id_dpto} value={d.id_dpto}>{d.nombre}</option>)}</select>{err("unidad")}</div>
        </div>
        <div><label>Misión</label><textarea rows={3} value={f.mision} onChange={set("mision")} disabled={ro} /></div>

        <div className="seccion">Especificación</div>
        <div className="form">
          <div><label>Categoría</label>
            <select value={f.categoria} onChange={set("categoria")} disabled={ro} className={errs.categoria ? "input-err" : ""}><option value="">Seleccionar…</option>
              {CATEGORIAS.map(([v, t]) => <option key={v} value={v}>{t}</option>)}</select>{err("categoria")}</div>
          <div><label>Educación requerida</label><input value={f.educacion} onChange={set("educacion")} disabled={ro} className={errs.educacion ? "input-err" : ""} maxLength={80} />{err("educacion")}</div>
          <div><label>Experiencia necesaria</label><input value={f.experiencia} onChange={set("experiencia")} disabled={ro} /></div>
        </div>

        <div className="seccion">Habilidades requeridas</div>
        <Casillas items={habilidades} idKey="id_habilidad" marcados={f.habilidades} onToggle={toggle("habilidades")} disabled={ro} />

        <div className="seccion">Conocimientos requeridos</div>
        <Casillas items={conocimientos} idKey="id_conocimiento" marcados={f.conocimientos} onToggle={toggle("conocimientos")} disabled={ro} />

        {ro ? (
          <div className="acciones"><button type="button" onClick={() => onClose(null)}>Aceptar</button></div>
        ) : (
        <div className="acciones">
          {/* Solo en el alta: al modificar, vaciar los datos cargados es riesgoso (para descartar está Cancelar) */}
          {!idPuesto && <button type="button" className="sec" onClick={limpiar} disabled={verificando || guardando}>Limpiar</button>}
          <span className="err" style={{ marginRight: "auto" }}>{error}</span>
          <button type="button" className="sec" onClick={() => onClose(null)}>Cancelar</button>
          <button disabled={verificando || guardando}>{guardando ? "Guardando…" : "Guardar"}</button>
        </div>
        )}
      </form>
    </div>
    {verPosiciones && (
      <Posiciones titulo={tituloPuesto} inicial={f.posiciones} soloLectura={ro} onCancel={() => setVerPosiciones(false)}
        onAceptar={(posiciones) => { setF({ ...f, posiciones }); setVerPosiciones(false); setError(""); }} />
    )}
  </>);
}

export default function Puestos() {
  const [list, setList] = useState([]);
  const [modal, setModal] = useState(null); // { id: null (alta) | id_puesto, inicial, ver: bool }
  // Formulario a medio cargar (se conserva al cerrar con click afuera). Uno solo: abrir otro puesto lo reemplaza.
  const [borrador, setBorrador] = useState(null);
  const [aviso, setAviso] = useState("");
  const [departamentos, setDepartamentos] = useState([]);
  const [habilidades, setHabilidades] = useState([]);
  const [conocimientos, setConocimientos] = useState([]);
  const canEdit = ["admin", "rrhh"].includes(localStorage.getItem("rol"));

  const load = () => api.get("/puestos").then((r) => setList(r.data));
  useEffect(() => { load(); }, []);
  useEffect(() => { // catálogos: los usa el modal también en modo "Ver" (todos los roles)
    api.get("/departamentos").then((r) => setDepartamentos(r.data));
    api.get("/habilidades").then((r) => setHabilidades(r.data));
    api.get("/conocimientos").then((r) => setConocimientos(r.data));
  }, []);
  async function ver(id) { // mismo modal, en solo lectura; no toca el borrador
    setAviso("");
    const d = (await api.get(`/puestos/${id}`)).data;
    setModal({ id, ver: true, inicial: { f: desdeDetalle(d), codigoEstado: "idle", intentado: false } });
  }

  function nuevo() {
    setAviso("");
    setModal({ id: null, inicial: borrador?.id === null ? borrador : null });
  }
  async function modificar(id) {
    setAviso("");
    if (borrador?.id === id) return setModal({ id, inicial: borrador });
    setBorrador(null); // el borrador de otro puesto (o del alta) se descarta
    const d = (await api.get(`/puestos/${id}`)).data;
    setModal({ id, inicial: { f: desdeDetalle(d), codigoEstado: "ok", intentado: false } });
  }
  function cerrar(b) { if (!modal.ver) setBorrador(b && { ...b, id: modal.id }); setModal(null); }
  function guardado(texto) {
    setBorrador(null); setModal(null); setAviso(texto); load();
  }

  return (
    <>
      <div className="encabezado">
        <h2>Puestos de trabajo</h2>
        <div className="acciones" style={{ alignItems: "center" }}>
          {aviso && <span className="ok">{aviso}</span>}
          {canEdit && <button onClick={nuevo}>Nuevo</button>}
        </div>
      </div>
      {modal && <PuestoForm key={`${modal.ver ? "ver" : "editar"}-${modal.id}`} idPuesto={modal.id} inicial={modal.inicial}
        soloLectura={modal.ver} departamentos={departamentos}
        habilidades={habilidades} conocimientos={conocimientos} onClose={cerrar} onGuardado={guardado} />}
      <div className="card">
        <table>
          <thead><tr><th>Código</th><th>Título</th><th>Unidad</th><th className="centro" style={{ whiteSpace: "nowrap" }}>Posiciones<br /><small>ocupadas / total</small></th><th className="centro">Acciones</th></tr></thead>
          <tbody>{list.map((p) => (
            <tr key={p.id_puesto}><td>{p.codigo}</td><td>{p.titulo}</td><td>{p.departamento}</td><td className="centro">{p.ocupadas} / {p.posiciones}</td>
              <td className="centro" style={{ whiteSpace: "nowrap" }}>
                <button onClick={() => ver(p.id_puesto)}>Ver</button>
                {canEdit && <> <button className="sec" onClick={() => modificar(p.id_puesto)}>Modificar</button></>}
              </td></tr>
          ))}</tbody>
        </table>
      </div>
    </>
  );
}
