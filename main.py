"""Citas - Centro de Salud Puruay Alto (UAIN1288P). Paradigmas: estructurado, orientado a objetos, funcional y por eventos."""
import hashlib, re
from collections import namedtuple
from datetime import datetime
from functools import reduce
from tkinter import Tk, Text, Frame, Button, simpledialog, messagebox

class DatoInvalidoError(Exception): """Error propio: el dato ingresado no tiene el formato correcto."""
class Cancelado(Exception): """El usuario cerró el cuadro de diálogo."""

REGLAS = {  # PARADIGMA ESTRUCTURADO. Tipo de dato: (patrón permitido, mensaje de error)
    "texto": (r".+", "Este dato no puede estar vacío."),
    "dni": (r"\d{8}", "El DNI debe tener 8 dígitos."),
    "telefono": (r"\d{9}", "El teléfono debe tener 9 dígitos."),
    "fecha": (r"\d{2}/\d{2}/\d{4}", "Use el formato dia/mes/año."),
    "hora": (r"\d{2}:\d{2}", "Use el formato HH:MM (24 horas)."),
}
def validar(tipo, valor):  # devuelve el valor si es correcto; si no, lanza DatoInvalidoError
    patron, mensaje = REGLAS[tipo]
    if not re.fullmatch(patron, valor): raise DatoInvalidoError(mensaje)
    try:
        if tipo == "fecha": datetime.strptime(valor, "%d/%m/%Y")  # rechaza fechas imposibles (31/02)
        if tipo == "hora": datetime.strptime(valor, "%H:%M")      # rechaza horas imposibles (25:70)
    except ValueError:
        raise DatoInvalidoError(mensaje)
    return valor

def hash_dni(dni): return hashlib.sha256(dni.encode()).hexdigest()  # el DNI real nunca se guarda (Ley N.° 29733)

Atencion = namedtuple("Atencion", "fecha motivo diagnostico medico")  # PARADIGMA OO. Tupla: no se puede modificar

class HistorialMedico:  # Composición: el historial pertenece a un Paciente y no existe sin él
    def __init__(self): self._atenciones = []  # protegido (_)
    def agregar(self, atencion): self._atenciones.append(atencion)
    def __str__(self):
        return "\n".join(f"{i}. {a.fecha} | {a.motivo} | Dx: {a.diagnostico} | {a.medico}" for i, a in enumerate(self._atenciones, 1)) or "Sin atenciones registradas."

class Persona:  # Clase base: datos comunes de cualquier persona
    def __init__(self, nombres, apellidos): self._nombres, self._apellidos = nombres, apellidos
    @property
    def nombre_completo(self): return f"{self._nombres} {self._apellidos}"
    def __str__(self): return self.nombre_completo

class Paciente(Persona):  # Clase derivada: guarda el hash del DNI (privado) y solo los últimos 4 dígitos
    def __init__(self, nombres, apellidos, dni_hash, dni4, fecha_nac, telefono):
        super().__init__(nombres, apellidos)
        self.__dni_hash, self.__telefono = dni_hash, telefono  # privados (__)
        self._dni4, self._fecha_nac, self.historial = dni4, fecha_nac, HistorialMedico()  # protegidos (_) y público
    @property
    def dni_hash(self): return self.__dni_hash
    @property
    def telefono(self): return "*" * 6 + self.__telefono[-3:]  # getter: muestra el teléfono enmascarado
    @telefono.setter
    def telefono(self, nuevo): self.__telefono = validar("telefono", nuevo)  # setter: valida antes de guardar
    def __str__(self):  # sobreescritura: amplía el __str__ de Persona
        return f"{super().__str__()} | DNI: ****{self._dni4} | Nac.: {self._fecha_nac} | Tel.: {self.telefono}"

class Cita:
    def __init__(self, paciente, fecha, hora, motivo, medico):
        self.paciente, self.fecha, self.hora, self.motivo, self.medico, self.diagnostico = paciente, fecha, hora, motivo, medico, None
        self._estado = "programada"  # protegido: solo cambia con marcar_atendida()
    @property
    def estado(self): return self._estado
    def marcar_atendida(self, diagnostico):
        self._estado, self.diagnostico = "atendida", diagnostico
        self.paciente.historial.agregar(Atencion(self.fecha, self.motivo, diagnostico, self.medico))
    def __str__(self):
        texto = f"[{self.estado.upper()}] {self.fecha} {self.hora} | {self.medico} | {self.motivo}\n   Paciente: {self.paciente}"
        return texto + (f"\n   Diagnóstico: {self.diagnostico}" if self.diagnostico else "")

class FabricaEntidades:  # Patrón Factory: crea los pacientes en un solo lugar y protege el DNI
    def crear_paciente(self, nombres, apellidos, dni, fecha_nac, telefono):
        return Paciente(nombres, apellidos, hash_dni(dni), dni[-4:], fecha_nac, telefono)

class Repositorio:  # Clase base + patrón Singleton: cada repositorio tiene una única instancia compartida
    _instancia = None
    def __new__(cls):
        if cls._instancia is None:  # si no existe se crea; si ya existe se reutiliza
            cls._instancia = super().__new__(cls)
            cls._instancia._items = []
        return cls._instancia
    def registrar(self, item): self._items.append(item)
    def listar(self): return list(self._items)
    def limpiar(self): self._items.clear()

class RepositorioPacientes(Repositorio):
    _instancia = None
    def buscar_por_dni(self, dni): return next((p for p in self._items if p.dni_hash == hash_dni(dni)), None)  # compara hashes
    def registrar(self, paciente):  # polimorfismo: redefine registrar() de la clase base
        if any(p.dni_hash == paciente.dni_hash for p in self._items): raise DatoInvalidoError("Ya existe un paciente con ese DNI.")
        super().registrar(paciente)

class RepositorioCitas(Repositorio):
    _instancia = None
    def registrar(self, cita):  # polimorfismo + regla: un paciente no puede tener dos citas a la misma hora
        if any(c.paciente is cita.paciente and (c.fecha, c.hora) == (cita.fecha, cita.hora) for c in self._items):
            raise DatoInvalidoError("Este paciente ya tiene una cita en esa fecha y hora.")
        super().registrar(cita)
    def buscar_por_dni(self, dni): return list(filter(lambda c: c.paciente.dni_hash == hash_dni(dni), self._items))  # FILTER
    def filtrar_por_fecha(self, fecha): return list(filter(lambda c: c.fecha == fecha, self._items))  # FILTER
    def programadas(self): return list(filter(lambda c: c.estado == "programada", self._items))  # FILTER

def reporte_por_fecha(citas):  # PARADIGMA FUNCIONAL. Función pura: no modifica nada, solo calcula el texto
    atendidas = reduce(lambda total, c: total + 1 if c.estado == "atendida" else total, citas, 0)  # REDUCE: suma 1 por cada atendida
    medicos = ", ".join(sorted({c.medico for c in citas}))  # comprensión de conjunto: médicos sin repetir
    resumen = f"Total: {len(citas)} (atendidas: {atendidas}, programadas: {len(citas) - atendidas}). Médicos: {medicos}"
    return resumen + "\n\n" + "\n\n".join(map(str, citas))  # MAP: convierte cada cita en texto

class Interfaz:  # PARADIGMA POR EVENTOS (los criterios de aceptación CA1 a CA4 están marcados en los handlers)
    def __init__(self):
        self.pacientes, self.citas, self.fabrica = RepositorioPacientes(), RepositorioCitas(), FabricaEntidades()
        self.ventana = Tk(); self.ventana.title("Registro de Citas - Puruay Alto")
        self.ventana.report_callback_exception = self.mostrar_error  # Tkinter la llama si un botón lanza un error
        menu = Frame(self.ventana); menu.pack(side="left", fill="y", padx=10, pady=10)
        opciones = [("Registrar nueva cita", self.registrar_cita), ("Listar todas las citas", self.listar_citas),
                    ("Buscar citas por DNI", self.buscar_citas), ("Registrar atención", self.registrar_atencion),
                    ("Ver historial médico", self.ver_historial), ("Reporte por fecha", self.reporte), ("Salir", self.ventana.destroy)]
        for texto, handler in opciones: Button(menu, text=texto, width=24, pady=6, command=handler).pack(pady=3)  # EVENTO: clic -> handler
        self.pantalla = Text(self.ventana, font=("Consolas", 10), wrap="word")
        self.pantalla.pack(side="right", fill="both", expand=True, padx=(0, 10), pady=10)
        self.mostrar("Bienvenido al sistema de citas.\n\nElija una opción del menú.")
    def mostrar(self, texto):  # borra lo anterior y escribe el texto nuevo
        self.pantalla.delete("1.0", "end"); self.pantalla.insert("end", texto)
    def mostrar_error(self, tipo, error, traza):  # manejo de errores: la ventana no se cierra
        if tipo is not Cancelado: messagebox.showerror("Error", str(error))
    def pedir(self, mensaje, tipo="texto"):
        while True:  # repite hasta que el dato sea válido (CA2)
            valor = simpledialog.askstring("Dato", mensaje, parent=self.ventana)
            if valor is None: raise Cancelado()
            try: return validar(tipo, valor.strip())
            except DatoInvalidoError as error: messagebox.showerror("Dato inválido", str(error))
    def registrar_cita(self):
        dni = self.pedir("DNI (8 dígitos):", "dni")
        paciente = self.pacientes.buscar_por_dni(dni)
        es_nuevo = paciente is None
        if es_nuevo:  # si el paciente no existe, se piden sus datos y la fábrica lo crea
            nombres, apellidos = self.pedir("Paciente nuevo.\nNombres:"), self.pedir("Apellidos:")
            nacimiento = self.pedir("Fecha de nacimiento (dd/mm/aaaa):", "fecha")
            paciente = self.fabrica.crear_paciente(nombres, apellidos, dni, nacimiento, self.pedir("Teléfono (9 dígitos):", "telefono"))
        fecha, hora = self.pedir("Fecha de la cita (dia/mes/año):", "fecha"), self.pedir("Hora de la cita (HH:MM):", "hora")
        medico, motivo = self.pedir("Médico:"), self.pedir("Motivo:")
        self.citas.registrar(Cita(paciente, fecha, hora, motivo, medico))  # CA3: si el horario está ocupado lanza un error
        if es_nuevo: self.pacientes.registrar(paciente)
        self.mostrar("✔ Cita registrada correctamente.")  # CA1
    def listar_citas(self): self.mostrar("\n\n".join(map(str, self.citas.listar())) or "No hay citas registradas.")
    def buscar_citas(self): self.mostrar("\n\n".join(map(str, self.citas.buscar_por_dni(self.pedir("DNI (8 dígitos):", "dni")))) or "Sin citas.")
    def reporte(self):
        fecha = self.pedir("Fecha del reporte (dia/mes/año):", "fecha")
        citas = self.citas.filtrar_por_fecha(fecha)
        self.mostrar(f"REPORTE DEL {fecha}\n" + reporte_por_fecha(citas) if citas else f"No hay citas el {fecha}.")
    def registrar_atencion(self):
        pendientes = self.citas.programadas()
        if not pendientes: return self.mostrar("No hay citas programadas.")
        self.mostrar("CITAS PROGRAMADAS\n\n" + "\n".join(f"{i}. {c.fecha} {c.hora} - {c.paciente.nombre_completo} ({c.motivo})" for i, c in enumerate(pendientes, 1)))
        numero = simpledialog.askinteger("Atender", "Número de la cita a atender:", minvalue=1, maxvalue=len(pendientes), parent=self.ventana)
        if numero is None: return
        cita = pendientes[numero - 1]
        cita.marcar_atendida(self.pedir("Diagnóstico:"))  # CA4
        self.mostrar("✔ Atención registrada.\n\n" + str(cita))
    def ver_historial(self):
        paciente = self.pacientes.buscar_por_dni(self.pedir("DNI del paciente:", "dni"))
        self.mostrar(f"HISTORIAL MÉDICO\n{paciente}\n\n{paciente.historial}" if paciente else "Paciente no encontrado.")

if __name__ == "__main__": Interfaz().ventana.mainloop()