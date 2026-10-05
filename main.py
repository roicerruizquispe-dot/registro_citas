import hashlib, re
import tkinter as tk
from tkinter import simpledialog, messagebox
from datetime import datetime

class DatoInvalidoError(Exception): pass
class Cancelado(Exception): pass