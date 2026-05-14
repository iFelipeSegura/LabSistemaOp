# Actividad 5 - Sistema Multipropósito: Terminal, Hilos y Sincronización

Integrantes: Felipe Segura  
Fecha: 14 de Mayo 2026  
Asignatura: Sistemas Operativos

---

## ¿Qué hace el sistema?

Básicamente es un sistema cliente-servidor para manejar archivos de forma remota. El servidor atiende a varios clientes al mismo tiempo usando threads, y hay un demonio que va monitoreando una carpeta cada 10 segundos para mover archivos automáticamente.

Los archivos del proyecto son:
- `servidor.py` → el servidor que recibe conexiones
- `cliente.py` → el cliente con menú interactivo
- `demonio.py` → proceso que monitorea archivos solo

---

## Parte 1 - Preparación en Linux

Primero hay que crear las carpetas y los archivos de prueba. Abrir una terminal y correr esto:

```bash
# Crear carpetas
mkdir -p ~/servidor_archivos/entrada
mkdir -p ~/servidor_archivos/procesados
mkdir -p ~/servidor_archivos/logs

# Permisos
chmod 755 ~/servidor_archivos
chmod 755 ~/servidor_archivos/entrada
chmod 755 ~/servidor_archivos/procesados
chmod 755 ~/servidor_archivos/logs

# Crear 3 archivos con datos aleatorios
for i in 1 2 3; do
    cat /dev/urandom | tr -dc 'a-zA-Z0-9 \n' | head -c 500 > ~/servidor_archivos/entrada/archivo$i.txt
done
```

Para verificar que quedó bien:
```bash
ls -lh ~/servidor_archivos/entrada/
```

---

## Cómo ejecutar el sistema

Se necesitan 3 terminales abiertas al mismo tiempo.

### Terminal 1 - Servidor

```bash
python3 servidor.py
```

Dejarlo corriendo. Si aparece esto ya está funcionando:
```
Servidor escuchando en 0.0.0.0:9999 ...
```

### Terminal 2 - Demonio

```bash
python3 demonio.py
```

Este proceso queda revisando la carpeta `entrada/` cada 10 segundos. Para cerrarlo Ctrl+C.

### Terminal 3 (y 4) - Cliente

```bash
python3 cliente.py
```

Se puede abrir en dos terminales distintas para probar los dos clientes al mismo tiempo que pide la demostración.

---

## Cómo usar el cliente

Al conectarse aparece este menú:

```
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

Para subir un archivo (opción 4) hay que poner la ruta completa del archivo en el computador:
```
Ruta del archivo local a subir: /home/usuario/mi_archivo.txt
```

> Nota: solo funciona con archivos de texto, no binarios.

El cliente mantiene una sola conexión con el servidor durante toda la sesión. Solo se desconecta cuando se elige la opción 0.

---

## Preguntas de la guía

### ¿Cómo evitó condiciones de carrera en el servidor?

Se usaron dos `Lock` de Python (`threading.Lock`). Uno protege el archivo `registro.log` y otro protege las operaciones sobre los archivos (leer, copiar, mover). Cada vez que un thread quiere hacer alguna de esas operaciones, primero tiene que adquirir el lock. Si otro thread ya lo tiene, espera hasta que se libere. Así no hay dos threads escribiendo al mismo tiempo en el mismo archivo.

En el demonio se usó un `Semaphore(1)` que funciona igual que un mutex, pero se eligió así porque deja más claro que el objetivo es limitar a un thread procesando archivos a la vez, mientras los demás esperan su turno.

### ¿Qué ventajas tiene usar threads en lugar de procesos?

Para este caso los threads son mejores porque:

- Comparten la misma memoria, entonces pueden acceder a las mismas variables (como los locks) sin hacer nada especial
- Son más rápidos de crear que un proceso nuevo
- Consumen menos recursos del sistema
- La comunicación entre threads es directa, no hace falta pipes ni sockets internos

Si se usaran procesos separados, habría que usar mecanismos más complicados como `multiprocessing.Manager` para compartir los locks, lo que no tiene sentido para un servidor de archivos como este.

### Explique el método de sincronización elegido

Se usaron dos mecanismos:

**Lock (Mutex):** Se usa en el servidor para proteger el log y las operaciones de archivos. Un lock tiene dos estados: libre o tomado. Cuando un thread llama `lock.acquire()` toma el lock y los demás que intenten tomarlo quedan bloqueados hasta que el primero llame `lock.release()`. En el código se usa con `with lock_lock:` que hace acquire y release automáticamente aunque haya un error.

**Semáforo:** Se usa en el demonio. Un semáforo tiene un contador interno, en este caso inicializado en 1 (`Semaphore(1)`), que funciona igual que un mutex. La diferencia es que un semáforo podría inicializarse en 2 o 3 para permitir más threads simultáneos si fuera necesario, lo que lo hace más flexible para escalar.

Ambos evitan que dos threads accedan al mismo recurso al mismo tiempo, que es exactamente lo que produce corrupción de datos o logs desordenados.

---

## Problemas que tuvimos

- Al principio el cliente abría una conexión nueva por cada acción del menú, entonces el servidor veía a cada operación como un cliente distinto. Se arregló pasando el socket como parámetro a cada función en vez de crearlo dentro.

- El demonio al iniciarse procesaba los archivos que ya estaban en `entrada/` aunque no fueran nuevos. Se arregló cargando al inicio los archivos existentes como "conocidos" y solo procesando los que aparecen después.

---

## Estructura final de carpetas

```
~/servidor_archivos/
├── entrada/          ← archivos disponibles para los clientes
├── procesados/       ← archivos movidos por el demonio
├── logs/             ← directorio de logs
└── registro.log      ← registro de todas las operaciones
```

Para ver el log en tiempo real:
```bash
tail -f ~/servidor_archivos/registro.log
```
