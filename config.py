import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

# carga de variables de entorno desde el archivo .env
load_dotenv()

# directorio raíz del proyecto
root_dir = Path(__file__).resolve().parent

# configuración de Telegram
bot_token = os.getenv("BOT_TOKEN")
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")

# directorio base para archivos temporales (/temp/)
temp_dir = Path(os.getenv("TEMP_DIR", root_dir / "temp")).resolve()
temp_dir.mkdir(parents=True, exist_ok=True)

# configuración de FluidSynth y SoundFont
# se leen del .env; si no están definidos, busca en el PATH del sistema
soundfont_path = Path(os.getenv("SOUNDFONT_PATH", "")).resolve() if os.getenv("SOUNDFONT_PATH") else None

_env_fluidsynth = os.getenv("FLUIDSYNTH_BIN")
if _env_fluidsynth:
    fluidsynth_bin = Path(_env_fluidsynth).resolve() if Path(_env_fluidsynth).is_absolute() else _env_fluidsynth
else:
    fluidsynth_bin = shutil.which("fluidsynth") or "fluidsynth"

# limites de seguridad (en MB convertidos a bytes)
max_file_size_mb = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
max_file_size_bytes = max_file_size_mb * 1024 * 1024
