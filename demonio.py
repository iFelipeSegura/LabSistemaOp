"""
demonio.py - Proceso demonio que monitorea 'entrada' cada 10 segundos
             y mueve archivos nuevos a 'procesados' usando semáforos.
Guía 5: Sistema Multipropósito - Terminal, Hilos y Sincronización
"""

import os
import shutil
import time
import threading
import signal
import sys
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
BASE_DIR   = os.path.expanduser('~/servidor_archivos')
ENTRADA    = os.path.join(BASE_DIR, 'entrada')
PROCESADOS = os.path.join(BASE_DIR, 'procesados')
LOG_FILE   = os.path.join(BASE_DIR, 'registro.log')
INTERVALO  = 10   # segundos entre cada revisión

# ─────────────────────────────────────────────
# SINCRONIZACIÓN
# Semáforo: permite que solo 1 thread procese archivos a la vez.
# Esto evita condiciones de carrera si el servidor también mueve archivos.
# ─────────────────────────────────────────────
semaforo = threading.Semaphore(1)
log_lock = threading.Lock()

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────
def registrar(mensaje):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    linea = f"[{timestamp}] [DEMONIO] {mensaje}\n"
    with log_lock:
        with open(LOG_FILE, 'a') as f:
            f.write(linea)
    print(linea.strip())

# ─────────────────────────────────────────────
# PROCESAMIENTO DE UN ARCHIVO (en su propio thread)
# ─────────────────────────────────────────────
def procesar_archivo(nombre):
    """
    Adquiere el semáforo, mueve el archivo de entrada → procesados
    y registra la operación. Libera el semáforo al terminar.
    """
    semaforo.acquire()
    try:
        origen  = os.path.join(ENTRADA, nombre)
        destino = os.path.join(PROCESADOS, nombre)

        # Verificar que sigue existiendo (otro thread pudo procesarlo)
        if not os.path.isfile(origen):
            registrar(f"(Ya procesado por otro thread): {nombre}")
            return

        # Simular tiempo de procesamiento
        time.sleep(1)
        shutil.move(origen, destino)
        registrar(f"Procesado y movido: {nombre} → procesados/")

    except Exception as e:
        registrar(f"Error al procesar '{nombre}': {e}")
    finally:
        semaforo.release()

# ─────────────────────────────────────────────
# MONITOR PRINCIPAL
# ─────────────────────────────────────────────
archivos_conocidos = set()

def monitorear():
    """
    Revisa el directorio 'entrada' cada INTERVALO segundos.
    Para cada archivo nuevo, lanza un thread que lo procesa.
    """
    global archivos_conocidos

    registrar("Demonio iniciado. Monitoreando 'entrada'...")

    while True:
        try:
            actuales = set(os.listdir(ENTRADA))
            nuevos   = actuales - archivos_conocidos

            if nuevos:
                registrar(f"Nuevos archivos detectados: {nuevos}")
                for nombre in nuevos:
                    t = threading.Thread(
                        target=procesar_archivo,
                        args=(nombre,),
                        daemon=True,
                        name=f"proc-{nombre}"
                    )
                    t.start()

            archivos_conocidos = actuales - nuevos  # los que quedan en entrada

        except Exception as e:
            registrar(f"Error en monitoreo: {e}")

        time.sleep(INTERVALO)

# ─────────────────────────────────────────────
# MANEJO DE SEÑALES (Ctrl+C)
# ─────────────────────────────────────────────
def salir(sig, frame):
    registrar("Demonio detenido por señal.")
    sys.exit(0)

signal.signal(signal.SIGINT, salir)
signal.signal(signal.SIGTERM, salir)

# ─────────────────────────────────────────────
# ENTRADA
# ─────────────────────────────────────────────
if __name__ == '__main__':
    os.makedirs(ENTRADA, exist_ok=True)
    os.makedirs(PROCESADOS, exist_ok=True)

    # Cargar archivos ya existentes para no reprocesarlos
    archivos_conocidos = set(os.listdir(ENTRADA))
    registrar(f"Archivos ignorados al inicio (ya existentes): {archivos_conocidos}")

    monitorear()