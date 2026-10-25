import shutil
import uuid
from pathlib import Path
from typing import Tuple, Union, Optional
from config import root_dir

# carpeta base para almacenamiento temporal 
TEMP_BASE_DIR = root_dir / "temp"


class FileManager:
    """gestor de archivos temporales y sesiones de procesamiento"""

    def __init__(self, base_dir: Optional[Union[str, Path]] = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else TEMP_BASE_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_session_dir(self) -> Tuple[str, Path]:
        """
        genera una cadena UUID4 única, crea la subcarpeta correspondiente dentro
        de /temp/ y retorna una tupla con (session_id, session_path).
        """
        session_id = str(uuid.uuid4())
        session_path = (self.base_dir / session_id).resolve()
        session_path.mkdir(parents=True, exist_ok=True)
        return session_id, session_path

    def cleanup_session(self, session_or_path: Union[str, Path]) -> bool:
        """
        elimina los archivos transitorios y la carpeta de la sesión tras la entrega.
        acepta tanto el session_id (UUID) como una ruta Path / str absoluta o relativa.
        """
        if isinstance(session_or_path, (str, Path)):
            target_path = Path(session_or_path)
            # Si no es absoluta y no existe directamente, buscarla dentro de base_dir
            if not target_path.is_absolute() or not target_path.exists():
                candidate = (self.base_dir / str(session_or_path)).resolve()
                if candidate.exists():
                    target_path = candidate
                else:
                    target_path = target_path.resolve()
        else:
            return False

        if target_path.exists():
            if target_path.is_dir():
                shutil.rmtree(target_path, ignore_errors=True)
            else:
                target_path.unlink(missing_ok=True)
            return True

        return False

# funciones de conveniencia directas
_default_manager = FileManager()


def create_session_directory() -> Tuple[str, Path]:
    """
    función de conveniencia para generar un UUID4, crear la subcarpeta en /temp/
    y retornar (session_id, session_path).
    """
    return _default_manager.create_session_dir()


def cleanup(session_or_path: Union[str, Path]) -> bool:
    """
    función de conveniencia para borrar archivos y directorios transitorios de la sesión.
    """
    return _default_manager.cleanup_session(session_or_path)
