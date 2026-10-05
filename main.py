import hashlib, re
import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime

class DatoInvalidoError(Exception): pass
class Cancelado(Exception): pass

class Paciente:
    def __init__(self, nombres, apellidos, dni, fecha_nac, telefono):
        self.nombres, self.apellidos, self.fecha_nac, self._tel = nombres, apellidos, fecha_nac, telefono
        self._dni_hash, self._dni4, self.historial = hashlib.sha256(dni.encode()).hexdigest(), dni[-4:], []
    def coincide_dni(self, dni): return self._dni_hash == hashlib.sha256(dni.encode()).hexdigest()
    @property
    def nombre_completo(self): return f"{self.nombres} {self.apellidos}"
    def __str__(self):
        tel = "*" * (len(self._tel) - 3) + self._tel[-3:]
        return f"{self.nombre_completo} | DNI: ****{self._dni4} | Nac.: {self.fecha_nac} | Tel.: {tel}"

class Cita:
    def __init__(self, paciente, fecha, hora, motivo, medico):
        self.paciente, self.fecha, self.hora, self.motivo, self.medico = paciente, fecha, hora, motivo, medico
        self.estado, self.diagnostico = "programada", None

    def marcar_atendida(self, dx):
        self.estado, self.diagnostico = "atendida", dx
        self.paciente.historial.append(
            {"fecha": self.fecha, "motivo": self.motivo, "diagnostico": dx, "medico": self.medico})

    def __str__(self):
        s = (f"Cita [{self.estado.upper()}] - {self.fecha} {self.hora}\n"
             f"  Paciente : {self.paciente}\n  Médico   : {self.medico}\n  Motivo   : {self.motivo}")
        return s + (f"\n  Diagnóstico: {self.diagnostico}" if self.diagnostico else "")

class RepositorioPacientes:
    def __init__(self): self._p = []

    def buscar_por_dni(self, dni): return next((p for p in self._p if p.coincide_dni(dni)), None)

    def registrar(self, p): self._p.append(p)

class RepositorioCitas:
    def __init__(self): self._c = []

    def existe_duplicada(self, p, fecha, hora):
        return any(c.paciente._dni_hash == p._dni_hash and c.fecha == fecha and c.hora == hora for c in self._c)

    def registrar(self, cita):
        if self.existe_duplicada(cita.paciente, cita.fecha, cita.hora):
            raise DatoInvalidoError("Este paciente ya tiene una cita en esa fecha y hora.")
        self._c.append(cita)

    def listar_todas(self): return list(self._c)

    def buscar_por_dni(self, dni): return [c for c in self._c if c.paciente.coincide_dni(dni)]

    def filtrar_por_fecha(self, f): return [c for c in self._c if c.fecha == f]

    def programadas(self): return [c for c in self._c if c.estado == "programada"]

def _validador(msg, ok):
    def v(x):
        if not ok(x): raise DatoInvalidoError(msg)
        return x
    return v

def _es_fecha(formato):
    def ok(x):
        try: return bool(datetime.strptime(x, formato))
        except ValueError: return False
    return ok

validar_dni = _validador("El DNI debe tener 8 dígitos.", lambda x: re.fullmatch(r"\d{8}", x))
validar_telefono = _validador("El teléfono debe tener 9 dígitos.", lambda x: re.fullmatch(r"\d{9}", x))
validar_fecha = _validador("Formato de fecha inválido (dd/mm/aaaa).", _es_fecha("%d/%m/%Y"))
validar_hora = _validador("Formato de hora inválido (HH:MM).", _es_fecha("%H:%M"))

rc, rp = RepositorioCitas(), RepositorioPacientes()
ventana = tk.Tk(); ventana.title("Registro de Citas"); ventana.geometry("820x480")
pantalla = tk.Text(ventana, font=("Consolas", 10), wrap="word", state="disabled")
def mostrar(texto):
    pantalla.config(state="normal"); pantalla.delete("1.0", "end")
    pantalla.insert("end", texto); pantalla.config(state="disabled")
def pedir(msg, validador=None):
    while True:
        v = simpledialog.askstring("Dato", msg, parent=ventana)
        if v is None: raise Cancelado()
        try:
            v = v.strip()
            if validador: return validador(v)
            if v: return v
            raise DatoInvalidoError("No puede estar vacío.")
        except DatoInvalidoError as e:
            messagebox.showerror("Error", str(e))
def ejecutar(f):
    try: f()
    except Cancelado: pass
def lista(citas, vacio, titulo):
    mostrar(f"{len(citas)} {titulo}:\n\n" + "\n\n".join(map(str, citas)) if citas else vacio)

def registrar_cita():
    dni = pedir("DNI (8 dígitos):", validar_dni)
    p = rp.buscar_por_dni(dni)
    nuevo = None
    if not p:
        nombres = pedir("Paciente nuevo.\nNombres:")
        apellidos = pedir("Apellidos:")
        fnac = pedir("Fecha de nacimiento (dd/mm/aaaa):", validar_fecha)
        tel = pedir("Teléfono (9 dígitos):", validar_telefono)
        p = nuevo = Paciente(nombres, apellidos, dni, fnac, tel)
    while True:
        fecha = pedir("Fecha de la cita (dd/mm/aaaa):", validar_fecha)
        hora = pedir("Hora de la cita (HH:MM):", validar_hora)
        if not rc.existe_duplicada(p, fecha, hora): break
        messagebox.showerror("Error", "Ya existe una cita para ese paciente en esa fecha y hora.")
    medico = pedir("Médico:")
    motivo = pedir("Motivo:")
    if nuevo: rp.registrar(nuevo)
    rc.registrar(Cita(p, fecha, hora, motivo, medico))
    mostrar("✔ Cita registrada correctamente.")

def listar_citas():
    lista(rc.listar_todas(), "No hay citas registradas.", "cita(s) registrada(s)")
def buscar_por_dni():
    lista(rc.buscar_por_dni(pedir("DNI a buscar (8 dígitos):", validar_dni)),
          "No se encontraron citas.", "cita(s) encontrada(s)")
def reporte_por_fecha():
    fecha = pedir("Fecha (dd/mm/aaaa):", validar_fecha)
    lista(rc.filtrar_por_fecha(fecha), f"Sin citas para el {fecha}.", f"cita(s) el {fecha}")