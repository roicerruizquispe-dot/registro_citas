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