# M.I.P. - Motor de Interpretación de Partituras

Bot de Telegram desarrollado en Python para procesar, validar y sintetizar archivos MIDI (`.mid`, `.midi`), transformándolos en maquetas de audio optimizadas y reproducibles al instante mediante **FluidSynth**, SoundFonts (`.sf2`) y **FFmpeg**.

---

## Características

- **Validación robusta:** Comprobación estricta de extensiones, límites de peso configurables e inspección estructural de eventos y cabeceras MIDI (`MThd`) mediante `mido`.
- **Extracción de metadatos:** Detección de pistas, tempo, notas procesables, canales activos y programas/instrumentos asignados.
- **Síntesis sonora de alta calidad:** Renderizado rápido de MIDI a WAV utilizando **FluidSynth** con bancos de sonido SoundFont 2 (`.sf2`).
- **Compresión y optimización de audio:** Conversión y normalización de volumen a OGG (Opus) optimizado para mensajes de voz de Telegram con **FFmpeg** / `pydub`.
- **Ciclo de vida efímero y seguro:** Directorios temporales aislados por sesión identificados con UUID4 y limpieza automática tras el procesamiento.
- **Rendimiento asíncrono:** Delegación de tareas pesadas de síntesis y compresión a ejecutores en segundo plano (`loop.run_in_executor`) sobre **Pyrogram**.

---

## Requisitos Previos

1. **Python 3.10+**
2. **FluidSynth**: Motor sintetizador por software.
   - *Windows:* Descargar binarios precompilados de [FluidSynth releases](https://github.com/FluidSynth/fluidsynth/releases).
   - *Linux (Ubuntu/Debian):* `sudo apt install fluidsynth`
   - *macOS:* `brew install fluidsynth`
3. **SoundFont (.sf2)**: Banco de muestras compatible (ej. `FluidR3_GM.sf2`, `GeneralUser GS`, etc.).
4. **FFmpeg**: Necesario para la compresión y conversión de audio mediante `pydub`.
   - Asegúrate de que `ffmpeg` y `ffprobe` estén en el `PATH` de tu sistema.
5. **Credenciales de Telegram**:
   - `BOT_TOKEN`: Obtenido a través de [@BotFather](https://t.me/BotFather).
   - `API_ID` y `API_HASH`: Obtenidos desde [my.telegram.org](https://my.telegram.org).

---

## Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/Snex-21/MIP.git
   cd MIP
   ```

2. **Crear y activar un entorno virtual:**
   ```bash
   # en Windows
   python -m venv venv
   .\venv\Scripts\activate

   # en Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias de Python:**
   ```bash
   pip install -r requirements.txt
   ```

---

## Configuración

Copia el archivo de ejemplo `.env.example` a un archivo `.env`:

```bash
cp .env.example .env
```

Edita `.env` con tus credenciales y rutas locales:

```env
# credenciales del Bot de Telegram
BOT_TOKEN=tu_bot_token_aqui
API_ID=tu_api_id_aqui
API_HASH=tu_api_hash_aqui

# motor de síntesis de audio
# ruta al archivo de SoundFont (.sf2)
SOUNDFONT_PATH=C:\fluidsynth\soundfonts\FluidR3_GM.sf2 # ejemplo

# ruta al ejecutable de FluidSynth (o 'fluidsynth' si está en el PATH)
FLUIDSYNTH_BIN=C:\fluidsynth\bin\fluidsynth.exe # ejemplo

# Tamaño máximo permitido en MB para archivos entrantes
MAX_FILE_SIZE_MB=10
```

---

## Ejecución

Inicia el bot ejecutando el script principal:

```bash
python bot.py
```

---

## Modo de Uso

1. Inicia una conversación con el bot en Telegram y presiona `/start`.
2. Envía cualquier archivo con extensión `.mid` o `.midi`.
3. El bot:
   - Descargará y validará la estructura de la partitura.
   - Sintetizará el audio utilizando el SoundFont configurado.
   - Comprimirá el resultado y te devolverá una nota de audio con la duración, conteo de notas y pistas detectadas.

---

## Estructura del Proyecto

```text
MIP/
├── handlers/
│   └── document_handler.py   # Manejo del flujo completo de recepción y entrega en Telegram
├── services/
│   ├── audio_service.py      # Compresión, normalización y conversión a OGG/MP3 con FFmpeg
│   ├── midi_service.py       # Lectura de metadatos, pistas e inspección con mido
│   └── synth_service.py      # Síntesis sonora de MIDI a WAV con FluidSynth
├── utils/
│   ├── file_manager.py       # Gestión y limpieza de carpetas de sesión temporal (UUID4)
│   └── validators.py         # Validaciones de extensión, peso y estructura de partituras
├── bot.py                    # Punto de entrada y configuración del cliente Pyrogram
├── config.py                 # Carga de variables de entorno y rutas del sistema
├── .env.example              # Plantilla de variables de entorno requeridas
├── requirements.txt          # Dependencias de Python
└── LICENSE                   # Licencia del proyecto
```

---

## Licencia

Este proyecto está bajo los términos de la licencia MIT. Consulta el archivo [LICENSE](LICENSE) para más detalles.

