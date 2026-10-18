# Analizador de representación de datos

Aplicación web hecha con **Python 3.12 y Django** que relaciona tres ideas del curso: los sistemas numéricos, la codificación de caracteres y la ejecución en contenedores.

- **Convertidor numérico:** recibe un número en base 2, 8, 10 o 16 (valores de 0 a 65 535) y lo muestra en decimal, binario, octal y hexadecimal. El binario se completa al siguiente límite de byte y se indican los bits significativos y los bytes necesarios.
- **Analizador de texto:** recibe hasta 20 caracteres y muestra, para cada uno, el carácter, su código decimal, su punto de código `U+`, su valor hexadecimal y sus bytes en UTF-8.

## Estructura del proyecto

```
.
├── manage.py
├── requirements.txt
├── Dockerfile
├── compose.yaml
├── config/                  # Proyecto Django (settings, urls, wsgi)
└── representacion/          # Aplicación Django
    ├── services.py          # Lógica pura: conversión, validación y análisis UTF-8
    ├── forms.py             # Formularios que usan los servicios
    ├── views.py             # Vista única con los dos formularios
    ├── urls.py
    ├── tests.py             # 22 pruebas automatizadas
    └── templates/representacion/index.html
```

La lógica de negocio está en `services.py`, separada de Django, para poder probarla sin levantar el servidor. Los formularios y la vista solo la conectan con la página.

La aplicación no guarda datos, por eso no usa base de datos, sesiones ni autenticación (`DATABASES = {}`).

## Reglas de validación

| Situación | Mensaje |
|---|---|
| Campo vacío | «Ingresa un número. El campo no puede estar vacío.» |
| Dígito que no pertenece a la base | «El dígito '2' no es válido en base 2 (binaria). Dígitos permitidos: 0 y 1.» |
| Valor negativo | «No se aceptan valores negativos. Ingresa un número entre 0 y 65 535.» |
| Fuera de rango | «El valor 65536 está fuera del rango permitido (0 a 65 535).» |
| Texto vacío o de más de 20 caracteres | Mensajes equivalentes en el formulario de texto |

Decisiones de diseño:

- El 0 se representa con **1 bit significativo** y ocupa 1 byte.
- Un «carácter» es un punto de código Unicode. Un emoji cuenta como 1 carácter; una letra con tilde escrita como letra base más acento combinado contaría como 2.
- El hexadecimal acepta mayúsculas y minúsculas.

## Ejecución local (sin Docker)

```bash
python3.12 -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver
```

Abre http://localhost:8000.

## Pruebas automatizadas

```bash
python manage.py test -v 2
```

Hay 22 pruebas que cubren: conversiones válidas desde las cuatro bases, ajuste a 8 y 16 bits, el caso del 0 y los límites del rango, entradas vacías, dígitos inválidos, negativos, valores fuera de rango, el caso `ñ` en UTF-8 (`U+00F1`, bytes `C3 B1`) y el comportamiento de la vista.

## Docker

### Construir y ejecutar con Compose

```bash
docker compose build
docker compose up -d
docker compose ps
```

La aplicación queda en http://localhost:8000. Para detenerla:

```bash
docker compose down
```

### Alternativa con `docker build` y `docker run`

```bash
docker build -t analizador-representacion:1.0 .
docker run -d --name analizador -p 8000:8000 \
  --memory=256m --cpus=1 \
  analizador-representacion:1.0
```

### Límites de recursos

`compose.yaml` define `mem_limit: 256m` y `cpus: 1.0`. Para comprobar que se aplicaron:

```bash
docker stats analizador --no-stream
docker inspect analizador --format 'Memoria: {{.HostConfig.Memory}} bytes, CPU: {{.HostConfig.NanoCpus}} nanoCPUs'
```

En la columna `MEM USAGE / LIMIT` de `docker stats` debe aparecer un límite de `256MiB`. En `docker inspect`, `Memory` debe valer `268435456` y `NanoCpus` debe valer `1000000000`.

### Evidencia de `docker stats`

> Pega aquí la salida real de `docker stats analizador --no-stream` o enlaza la captura guardada en `evidencias/docker-stats.png`.

```
(pendiente: pegar la salida obtenida en tu equipo)
```

## Arquitectura de Von Neumann: qué recursos usa la aplicación

En el modelo de Von Neumann, programas y datos comparten una misma memoria y la **CPU** ejecuta instrucciones tomadas de ella.

- **CPU:** ejecuta las instrucciones del intérprete de Python, de Django y de nuestra lógica. Las conversiones usan aritmética entera y operaciones de bits, que la unidad aritmético-lógica resuelve directamente. El contenedor la limita a 1 CPU.
- **Memoria principal (RAM):** guarda el código del programa y los datos de cada petición (el número escrito, el texto, los resultados). Es el mismo espacio para instrucciones y datos, como describe el modelo. El contenedor la limita a 256 MB.
- **Entrada/salida:** el navegador envía los formularios por la red (entrada) y recibe la página con los resultados (salida). El teclado y la pantalla del usuario cierran ese circuito.
- **Almacenamiento:** solo se usa para leer el código y las dependencias al arrancar. La aplicación no escribe datos.
- **Representación binaria:** todo lo que se muestra existe en memoria como bits. Un número ocupa un número entero de bytes y un texto se almacena como bytes UTF-8, por eso `ñ` (`U+00F1`) ocupa 2 bytes (`C3 B1`) y `A` ocupa 1.

## Por qué el contenedor comparte el kernel del host

Un contenedor no es una máquina virtual: no trae su propio sistema operativo completo ni su propio kernel. Es un **proceso del host** aislado con dos mecanismos del kernel de Linux:

- **Namespaces:** dan al proceso su propia vista de procesos, red y sistema de archivos, de modo que parece estar solo.
- **cgroups:** limitan y miden los recursos que puede consumir. Así se aplican los 256 MB y la 1 CPU del ejercicio.

La imagen `python:3.12-slim` solo aporta el espacio de usuario (bibliotecas, Python y las dependencias). Las llamadas al sistema que hace la aplicación, como reservar memoria o abrir un socket, las atiende el kernel del host. Por eso un contenedor arranca en segundos y consume menos recursos que una máquina virtual, aunque también ofrece menos aislamiento. En Windows y macOS, Docker Desktop ejecuta una pequeña máquina virtual Linux y los contenedores comparten el kernel de esa máquina virtual.

## Guion sugerido para el video (máximo 2 minutos)

1. **Conversión válida:** escribe `FF` en base 16 y muestra decimal, binario, octal, hexadecimal, bits y bytes.
2. **Ajuste a bytes:** convierte `256` en base 10 y señala que el binario ocupa 16 bits.
3. **Error de validación:** escribe `1012` en base 2 y muestra el mensaje.
4. **Texto con ñ:** analiza `año` y señala `U+00F1` y `C3 B1`.
5. **Pruebas:** ejecuta `python manage.py test` (o dentro del contenedor con `docker compose exec web python manage.py test`).
6. **Contenedor en ejecución:** muestra `docker compose ps` y `docker stats analizador --no-stream` con el límite de 256 MiB.

## Lista de entrega

- [ ] Repositorio de GitHub (o carpeta de Google Drive) con acceso público o por enlace
- [ ] `docker stats` pegado arriba o captura en `evidencias/`
- [ ] Video de máximo 2 minutos enlazado aquí: _(pega el enlace)_
