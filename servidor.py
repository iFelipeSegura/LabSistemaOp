"""
servidor.py - Servidor multihilo para gestión de archivos remotos
Guía 5: Sistema Multipropósito - Terminal, Hilos y Sincronización
"""

import socket
import threading
import os
import shutil
import json
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
HOST = '0.0.0.0'
PORT = 9999
BASE_DIR = os.path.expanduser('~/servidor_archivos')
ENTRADA   = os.path.join(BASE_DIR, 'entrada')
PROCESADOS = os.path.join(BASE_DIR, 'procesados')
LOGS      = os.path.join(BASE_DIR, 'logs')
LOG_FILE  = os.path.join(BASE_DIR, 'registro.log')

# ─────────────────────────────────────────────
# SINCRONIZACIÓN
# ─────────────────────────────────────────────
log_lock   = threading.Lock()   # Mutex para registro.log
file_lock  = threading.Lock()   # Mutex para operaciones de archivos

# ─────────────────────────────────────────────
# LOGGING SINCRONIZADO
# ─────────────────────────────────────────────
def registrar(mensaje):
    """Escribe en registro.log de forma thread-safe."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    linea = f"[{timestamp}] {mensaje}\n"
    with log_lock:
        with open(LOG_FILE, 'a') as f:
            f.write(linea)
    print(linea.strip())

# ─────────────────────────────────────────────
# MANEJADOR DE CADA CLIENTE (se ejecuta en su propio thread)
# ─────────────────────────────────────────────
def manejar_cliente(conn, addr):
    """Thread que atiende a un cliente conectado."""
    registrar(f"Cliente conectado: {addr}")
    try:
       while True:
            # Recibir solicitud (JSON) acumulando hasta el salto de línea
            buffer = b''
            while True:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                buffer += chunk
                if buffer.endswith(b'\n'):
                    break
            
            datos = buffer.decode('utf-8').strip()
            if not datos:
                break

            try:
                solicitud = json.loads(datos)
            except json.JSONDecodeError:
                conn.sendall(b'{"error": "Solicitud mal formada"}\n')
                continue

            accion = solicitud.get('accion', '')

            # ── LISTAR ARCHIVOS ──────────────────────────────
            if accion == 'listar':
                with file_lock:
                    archivos = os.listdir(ENTRADA)
                respuesta = {'archivos': archivos}
                registrar(f"{addr} listó archivos en entrada")

            # ── LEER CONTENIDO DE UN ARCHIVO ─────────────────
            elif accion == 'leer':
                nombre = solicitud.get('nombre', '')
                ruta = os.path.join(ENTRADA, nombre)
                if os.path.isfile(ruta):
                    with file_lock:
                        with open(ruta, 'r', errors='replace') as f:
                            contenido = f.read()
                    respuesta = {'contenido': contenido}
                    registrar(f"{addr} leyó archivo: {nombre}")
                else:
                    respuesta = {'error': f"Archivo '{nombre}' no encontrado"}

            # ── COPIAR ARCHIVO A PROCESADOS ───────────────────
            elif accion == 'copiar':
                nombre = solicitud.get('nombre', '')
                origen = os.path.join(ENTRADA, nombre)
                destino = os.path.join(PROCESADOS, nombre)
                if os.path.isfile(origen):
                    with file_lock:
                        shutil.copy2(origen, destino)
                    respuesta = {'ok': f"Archivo '{nombre}' copiado a procesados"}
                    registrar(f"{addr} copió archivo: {nombre} → procesados")
                else:
                    respuesta = {'error': f"Archivo '{nombre}' no encontrado"}

            # ── SUBIR ARCHIVO AL SERVIDOR ─────────────────────
            elif accion == 'subir':
                nombre = solicitud.get('nombre', '')
                contenido = solicitud.get('contenido', '')
                ruta = os.path.join(ENTRADA, nombre)
                with file_lock:
                    with open(ruta, 'w') as f:
                        f.write(contenido)
                respuesta = {'ok': f"Archivo '{nombre}' subido a entrada"}
                registrar(f"{addr} subió archivo: {nombre}")

            # ── DESCARGAR ARCHIVO DEL SERVIDOR ───────────────
            elif accion == 'descargar':
                nombre = solicitud.get('nombre', '')
                # Buscar en entrada o procesados
                for carpeta in [ENTRADA, PROCESADOS]:
                    ruta = os.path.join(carpeta, nombre)
                    if os.path.isfile(ruta):
                        with file_lock:
                            with open(ruta, 'r', errors='replace') as f:
                                contenido = f.read()
                        respuesta = {'contenido': contenido, 'nombre': nombre}
                        registrar(f"{addr} descargó archivo: {nombre}")
                        break
                else:
                    respuesta = {'error': f"Archivo '{nombre}' no encontrado"}

            # ── VER LOGS ──────────────────────────────────────
            elif accion == 'logs':
                with log_lock:
                    if os.path.isfile(LOG_FILE):
                        with open(LOG_FILE, 'r') as f:
                            contenido = f.read()
                    else:
                        contenido = "(log vacío)"
                respuesta = {'logs': contenido}

            else:
                respuesta = {'error': f"Acción desconocida: '{accion}'"}

            # Enviar respuesta
            conn.sendall((json.dumps(respuesta) + '\n').encode('utf-8'))

    except ConnectionResetError:
        pass
    finally:
        conn.close()
        registrar(f"Cliente desconectado: {addr}")

# ─────────────────────────────────────────────
# SERVIDOR PRINCIPAL
# ─────────────────────────────────────────────
def iniciar_servidor():
    # Asegurar que existan los directorios
    for d in [ENTRADA, PROCESADOS, LOGS]:
        os.makedirs(d, exist_ok=True)

    registrar("=== Servidor iniciado ===")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        s.listen()
        print(f"Servidor escuchando en {HOST}:{PORT} ...")

        while True:
            conn, addr = s.accept()
            # Cada cliente se maneja en su propio thread
            t = threading.Thread(target=manejar_cliente, args=(conn, addr), daemon=True)
            t.start()
            print(f"[Threads activos: {threading.active_count() - 1}]")

if __name__ == '__main__':
    iniciar_servidor()