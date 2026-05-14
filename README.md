# LabSistemaOp
# Sistema Multipropósito — Guía 5
**Terminal Linux · Sockets · Hilos · Sincronización**

---

## Estructura del proyecto

```
proyecto/
├── servidor.py       # Servidor multihilo con sockets
├── cliente.py        # Cliente interactivo con conexión persistente
├── demonio.py        # Demonio de monitoreo automático
└── README.md

~/servidor_archivos/  # Creado automáticamente al iniciar
├── entrada/          # Archivos disponibles en el servidor
├── procesados/       # Archivos movidos por el demonio
├── logs/             # Directorio de logs
└── registro.log      # Registro de todas las operaciones
```

---

## Requisitos

- Python 3.8 o superior
- Sin dependencias externas (solo biblioteca estándar)

---

## Preparación del entorno (Linux)

Antes de ejecutar los scripts, crear la estructura de carpetas y los archivos de prueba:

```bash
# Crear directorios
mkdir -p ~/servidor_archivos/entrada
mkdir -p ~/servidor_archivos/procesados
mkdir -p ~/servidor_archivos/logs

# Asignar permisos
chmod 755 ~/servidor_archivos
chmod 755 ~/servidor_archivos/entrada
chmod 755 ~/servidor_archivos/procesados
chmod 755 ~/servidor_archivos/logs

# Generar 3 archivos de prueba con datos aleatorios
for i in 1 2 3; do
    cat /dev/urandom | tr -dc 'a-zA-Z0-9 \n' | head -c 500 \
        > ~/servidor_archivos/entrada/archivo$i.txt
done
```

---

## Modo de uso

Se necesitan **hasta 3 terminales** abiertas simultáneamente.

### Terminal 1 — Iniciar el servidor

```bash
python3 servidor.py
```

El servidor queda escuchando en `0.0.0.0:9999`. Cada cliente que se conecta recibe su propio thread. No cerrar esta terminal mientras se use el sistema.

Salida esperada:
```
Servidor escuchando en 0.0.0.0:9999 ...
[2026-05-14 12:00:01] === Servidor iniciado ===
```

---

### Terminal 2 — Iniciar el demonio (opcional)

```bash
python3 demonio.py
```

El demonio monitorea `~/servidor_archivos/entrada/` cada 10 segundos. Cuando detecta archivos nuevos, los mueve automáticamente a `procesados/` usando un semáforo para evitar condiciones de carrera.

Para detenerlo: `Ctrl + C`

Salida esperada:
```
[12:00:00] [DEMONIO] Demonio iniciado. Monitoreando 'entrada'...
[12:00:10] [DEMONIO] Nuevos archivos detectados: {'nuevo.txt'}
[12:00:11] [DEMONIO] Procesado y movido: nuevo.txt → procesados/
```

---

### Terminal 3 — Conectar un cliente

```bash
python3 cliente.py
```

El cliente establece **una sola conexión persistente** con el servidor durante toda la sesión. Al iniciar muestra el menú:

```
✓ Conectado al servidor 127.0.0.1:9999

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
```

#### Opciones del menú

| Opción | Acción | Ejemplo de uso |
|--------|--------|----------------|
| 1 | Listar archivos en `entrada/` | Solo presionar 1 + Enter |
| 2 | Leer contenido de un archivo | Ingresar nombre: `archivo1.txt` |
| 3 | Copiar archivo a `procesados/` | Ingresar nombre: `archivo1.txt` |
| 4 | Subir un archivo local al servidor | Ingresar ruta: `/home/usuario/datos.txt` |
| 5 | Descargar un archivo del servidor | Ingresar nombre y destino local |
| 6 | Ver el registro de operaciones | Solo presionar 6 + Enter |
| 0 | Cerrar la conexión y salir | — |

---

### Probar con múltiples clientes simultáneos

Para demostrar el funcionamiento multihilo abrir dos terminales adicionales y ejecutar `cliente.py` en cada una:

```bash
# Terminal 3
python3 cliente.py

# Terminal 4 (al mismo tiempo)
python3 cliente.py
```

Ambos clientes serán atendidos en paralelo. El servidor mostrará el número de threads activos con cada nueva conexión.

---

### Subir un archivo al servidor

1. Tener un archivo de texto en el sistema local, por ejemplo:
```bash
echo "Contenido de prueba" > /home/$USER/mi_archivo.txt
```

2. En el cliente, seleccionar opción **4** e ingresar la ruta completa:
```
Ruta del archivo local a subir: /home/usuario/mi_archivo.txt
✓ Archivo 'mi_archivo.txt' subido a entrada
```

> Solo se admiten archivos de texto (.txt, .csv, .py, etc.)

---

## Conceptos implementados

| Concepto | Implementación |
|----------|---------------|
| Sockets TCP | `socket.AF_INET` + `SOCK_STREAM` en servidor y cliente |
| Multithreading | `threading.Thread` — un thread por cliente conectado |
| Mutex (Lock) | Protege escrituras en `registro.log` y operaciones de archivos |
| Semáforo | `threading.Semaphore(1)` en el demonio — evita que dos threads muevan el mismo archivo |
| Proceso demonio | Bucle infinito con `signal` para manejo de Ctrl+C |
| Protocolo | JSON sobre TCP con delimitador `\n` |

---

## Registro de operaciones

Todas las acciones quedan registradas en `~/servidor_archivos/registro.log`:

```
[2026-05-14 12:00:01] === Servidor iniciado ===
[2026-05-14 12:00:05] Cliente conectado: ('127.0.0.1', 52341)
[2026-05-14 12:00:08] ('127.0.0.1', 52341) listó archivos en entrada
[2026-05-14 12:00:12] ('127.0.0.1', 52341) leyó archivo: archivo1.txt
[2026-05-14 12:00:20] Cliente desconectado: ('127.0.0.1', 52341)
```

Para ver el log en tiempo real desde la terminal:
```bash
tail -f ~/servidor_archivos/registro.log
```
