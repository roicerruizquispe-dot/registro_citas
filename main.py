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