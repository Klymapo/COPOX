# Stylizer como página web independiente de tu PC

La interfaz ya permite cargar imágenes, generar modelos, consultar la cola, revisar resultados y descargar archivos desde un navegador. `server.py` permite alojar todo el servicio fuera de tu computadora, con una dirección HTTPS proporcionada por el alojamiento.

## Qué está implementado y qué falta activar

- Aplicación web adaptable al celular, acceso con usuario y contraseña, cola compartida e historial.
- Servidor HTTP con comprobación de salud en `/healthz` y un solo trabajador para evitar ejecuciones duplicadas.
- Imagen Docker con Python 3.11 y Blender 4.5.3, sin incluir claves, resultados ni archivos personales del repositorio.
- Datos y resultados separados dentro de un volumen persistente.
- Despliegue declarativo en `render.yaml` y arranque con Docker Compose en otro servidor.

**Añadir estos archivos a GitHub no publica la web.** Para obtener una URL real hay que conectar una cuenta de alojamiento y desplegar el servicio. El repositorio puede seguir siendo privado.

## Publicación en Render

El archivo `render.yaml` propone un servicio Docker de **1 CPU / 2 GB de RAM** con **5 GB de disco persistente**. Es una configuración de pago: revisa el importe que muestra Render antes de crearla. El código no contrata servicios ni modifica tu facturación. Los modelos grandes y la preparación de Blender pueden necesitar más memoria.

1. Conecta Render a tu cuenta y permite acceso al repositorio privado `Klymapo/stylizer`.
2. En Render, crea un **Blueprint** desde ese repositorio. Usa `main` después de integrar este cambio, o la rama `codex/stylizer-cloud-web` para probarlo antes. Render leerá `render.yaml`.
3. Introduce `STYLIZER_PASSWORD` como secreto: usa al menos **12 caracteres**. El usuario es `atatoriz`, modificable mediante `STYLIZER_USER`.
4. Revisa el plan y el disco propuestos, y confirma el despliegue solo si aceptas su costo.
5. Añade `HF_TOKEN` como secreto si lo necesita tu acceso a TRELLIS.2. Para generar imágenes desde texto añade `AGNES_API_KEY`. No hacen falta ambos para iniciar la web; los proveedores seguirán sujetos a sus cuotas y permisos.
6. Espera a que el servicio esté **Live** y copia la URL HTTPS que Render proporciona. Ábrela directamente en el navegador del celular e inicia sesión.

No abras un túnel desde tu PC ni ejecutes `app.py --mobile` para esta modalidad. Una vez publicado, el servidor realiza las tareas, incluso si tu PC está apagada.

Los despliegues automáticos están desactivados para evitar reinicios durante una generación. Actualiza manualmente cuando no haya tareas activas. Una tarea interrumpida por un reinicio queda marcada para reintento; no se vuelve a cobrar/solicitar automáticamente al proveedor.

### Almacenamiento

El disco se monta en `/app/storage`:

| Ruta | Contenido |
|---|---|
| `/app/storage/jobs` | SQLite, entradas duraderas y bloqueo del trabajador |
| `/app/storage/outputs` | GLB, imágenes, paquetes ZIP y revisiones |

Mantén ambas rutas en el disco persistente y usa **una sola instancia**. Un sistema de archivos efímero perdería datos al reiniciar. No borres el disco al actualizar la aplicación. Este almacenamiento no importa ni sincroniza automáticamente las generaciones que ya tengas en la PC.

Render Free no admite este disco persistente y se suspende por inactividad. Por esa razón no es la configuración propuesta para conservar tu trabajo. La disponibilidad y los precios se deben comprobar en el panel antes de activar recursos.

## Generación sin Ollama en tu computadora

El contenedor usa `STYLIZER_PROMPT_MODE=template`: añade a tu descripción instrucciones de pose, encuadre, iluminación y fondo. No hace una traducción ni una reformulación con un modelo de lenguaje. La imagen resultante sigue dependiendo de Agnes y requiere tu clave.

Puedes subir una imagen existente para saltarte por completo el paso de texto y Agnes. Blender está incluido en la imagen del servidor y prepara allí los GLB; no necesita acceder a tu Blender local.

El modo local conserva `STYLIZER_PROMPT_MODE=ollama`. Si quieres usarlo en un servidor, Ollama también debe estar disponible en ese entorno y `OLLAMA_URL` debe apuntar a él; `localhost` en la nube no es tu PC.

## Otro servidor con Docker

La imagen usa Linux x86_64, compatible con el módulo de Blender incluido. En otros tipos de CPU, Compose necesita emulación de esa arquitectura.

1. Copia `.env.example` a `.env` y establece una contraseña de al menos 12 caracteres.
2. Ejecuta `docker compose up -d --build`.
3. Usa un proxy HTTPS de tu alojamiento hacia `127.0.0.1:7860`.

Compose crea el volumen `stylizer-data` y reinicia el contenedor con el equipo. No uses `docker compose down -v` si quieres conservar los modelos: `-v` borra ese volumen.

El contenedor procesa un trabajo a la vez. El puerto puede venir de `PORT`, como en Render; `STYLIZER_PORT` tiene prioridad si se define. No es necesario publicar Ollama, Blender ni puertos de tu computadora.

## Prueba de aceptación desde el celular

1. Accede a la URL HTTPS mediante datos móviles, sin usar la Wi-Fi de casa.
2. Inicia sesión y sube una imagen en **Generar**.
3. Envía la tarea, cierra la pestaña y vuelve a entrar; debe aparecer en **Estado**.
4. Abre los resultados y comprueba la imagen, el visor 3D y la descarga del ZIP.
5. Si necesitas preparar el GLB, abre **Godot** y envía esa tarea.
6. Cuando no haya tareas activas, reinicia el servicio desde el alojamiento y confirma que los resultados siguen disponibles.

`/healthz` solo informa de si el trabajador está disponible; no expone el historial ni verifica credenciales o cuotas de los proveedores. La contraseña protege la API y las descargas. `.env` y la carpeta privada de trabajos quedan bloqueados incluso para descargas autenticadas.

## Verificación de esta implementación

Las pruebas HTTP usan el punto de entrada real `server.py`: inicio de sesión, salud, bloqueo de archivos privados, texto sin Ollama, cola y descarga del ZIP. Los proveedores de generación se simulan para no consumir cuota. Blender se prueba exportando e importando un GLB real. La publicación, TLS, permisos del disco y construcción final del contenedor deben comprobarse también en el alojamiento elegido.

## Referencias oficiales consultadas

- [Docker en Render](https://render.com/docs/docker)
- [Blueprints y su configuración](https://render.com/docs/blueprint-spec)
- [Discos persistentes](https://render.com/docs/disks)
- [Limitaciones del alojamiento gratuito](https://render.com/docs/free)
- [Precios de Render](https://render.com/pricing)
