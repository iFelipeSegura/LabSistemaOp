"""
cliente.py - Cliente interactivo con conexión persistente
Guía 5: Sistema Multipropósito - Terminal, Hilos y Sincronización
"""

import socket
import json
import os

# ─────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────
HOST = '127.0.0.1'
PORT = 9999

# ─────────────────────────────────────────────
# COMUNICACIÓN (usa el socket ya abierto)
# ─────────────────────────────────────────────
def enviar_solicitud(sock, solicitud: dict) -> dict:
    """Envía una solicitud JSON por el socket persistente y retorna la respuesta."""
    sock.sendall((json.dumps(solicitud) + '\n').encode('utf-8'))
    respuesta = b''
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            break
        respuesta += chunk
        if respuesta.endswith(b'\n'):
            break
    return json.loads(respuesta.decode('utf-8').strip())

# ─────────────────────────────────────────────
# ACCIONES DEL MENÚ
# ─────────────────────────────────────────────
def listar_archivos(sock):
    resp = enviar_solicitud(sock, {'accion': 'listar'})
    archivos = resp.get('archivos', [])
    if archivos:
        print("\nArchivos en 'entrada':")
        for i, nombre in enumerate(archivos, 1):
            print(f"  {i}. {nombre}")
    else:
        print("  (No hay archivos en entrada)")

def leer_archivo(sock):
    nombre = input("Nombre del archivo a leer: ").strip()
    resp = enviar_solicitud(sock, {'accion': 'leer', 'nombre': nombre})
    if 'contenido' in resp:
        print(f"\n── Contenido de '{nombre}' ──")
        print(resp['contenido'])
        print("────────────────────────────")
    else:
        print(f"Error: {resp.get('error')}")

def copiar_a_procesados(sock):
    nombre = input("Nombre del archivo a copiar a 'procesados': ").strip()
    resp = enviar_solicitud(sock, {'accion': 'copiar', 'nombre': nombre})
    if 'ok' in resp:
        print(f"✓ {resp['ok']}")
    else:
        print(f"Error: {resp.get('error')}")

def subir_archivo(sock):
    ruta_local = input("Ruta del archivo local a subir: ").strip()
    if not os.path.isfile(ruta_local):
        print("Error: el archivo local no existe.")
        return
    nombre = os.path.basename(ruta_local)
    with open(ruta_local, 'r', errors='replace') as f:
        contenido = f.read()
    resp = enviar_solicitud(sock, {'accion': 'subir', 'nombre': nombre, 'contenido': contenido})
    if 'ok' in resp:
        print(f"✓ {resp['ok']}")
    else:
        print(f"Error: {resp.get('error')}")

def descargar_archivo(sock):
    nombre = input("Nombre del archivo a descargar: ").strip()
    destino = input(f"Guardar como (Enter para usar '{nombre}'): ").strip() or nombre
    resp = enviar_solicitud(sock, {'accion': 'descargar', 'nombre': nombre})
    if 'contenido' in resp:
        with open(destino, 'w') as f:
            f.write(resp['contenido'])
        print(f"✓ Archivo guardado como '{destino}'")
    else:
        print(f"Error: {resp.get('error')}")

def ver_logs(sock):
    resp = enviar_solicitud(sock, {'accion': 'logs'})
    print("\n── registro.log ──────────────────────")
    print(resp.get('logs', '(vacío)'))
    print("──────────────────────────────────────")

# ─────────────────────────────────────────────
# MENÚ PRINCIPAL
# ─────────────────────────────────────────────
MENU = """
╔══════════════════════════════════╗
║   CLIENTE - Gestión de Archivos  ║
╠══════════════════════════════════╣
║  1. Listar archivos en entrada   ║
║  2. Leer contenido de un archivo ║
║  3. Copiar archivo a procesados  ║
║  4. Subir archivo al servidor    ║
║  5. Descargar archivo            ║
║  6. Ver logs de operaciones      ║
║  0. Salir                        ║
╚══════════════════════════════════╝
"""

ACCIONES = {
    '1': listar_archivos,
    '2': leer_archivo,
    '3': copiar_a_procesados,
    '4': subir_archivo,
    '5': descargar_archivo,
    '6': ver_logs,
}

def main():
    # Una sola conexión para toda la sesión
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        print(f"✓ Conectado al servidor {HOST}:{PORT}")
    except ConnectionRefusedError:
        print("Error: No se pudo conectar. ¿Está corriendo servidor.py?")
        return

    try:
        while True:
            print(MENU)
            opcion = input("Selecciona una opción: ").strip()
            if opcion == '0':
                print("¡Hasta luego!")
                break
            accion = ACCIONES.get(opcion)
            if accion:
                try:
                    accion(sock)
                except Exception as e:
                    print(f"Error: {e}")
            else:
                print("Opción inválida.")
    finally:
        sock.close()

if __name__ == '__main__':
    main()