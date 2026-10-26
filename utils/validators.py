from pathlib import Path
from typing import Tuple, Union, Optional
import mido

from config import max_file_size_bytes

# Extensiones permitidas 
ALLOWED_EXTENSIONS = {".mid", ".midi"}

# Límite máximo de tamaño de archivo
MAX_FILE_SIZE_BYTES = max_file_size_bytes


class ValidationError(Exception):
    """excepción personalizada para fallos de validación"""
    pass


class MIDIValidator:
    """validador de archivos y flujos de datos MIDI"""

    def __init__(
        self,
        file_path: Optional[Union[str, Path]] = None,
        max_size_bytes: int = MAX_FILE_SIZE_BYTES,
        allowed_extensions: Optional[set] = None
    ) -> None:
        self.file_path = Path(file_path) if file_path else None
        self.max_size_bytes = max_size_bytes
        self.allowed_extensions = allowed_extensions or ALLOWED_EXTENSIONS

    def validate_extension(self, filename: Optional[Union[str, Path]] = None) -> bool:
        """
        valida que el archivo tenga una extensión permitida (.mid, .midi)
        """
        path = Path(filename) if filename else self.file_path
        if not path:
            raise ValidationError("No se proporcionó ningún archivo para validar la extensión.")

        extension = path.suffix.lower()
        if extension not in self.allowed_extensions:
            raise ValidationError(
                f"Extensión no permitida: '{extension}'. Formatos aceptados: {', '.join(sorted(self.allowed_extensions))}"
            )
        return True

    def validate_file_size(self, file_size_or_path: Optional[Union[int, str, Path]] = None) -> bool:
        """
        valida que el tamaño del archivo no exceda el límite permitido para evitar saturación de almacenamiento o DoS.
        puede recibir el tamaño en bytes directamente o una ruta de archivo existente
        """
        size_bytes: int

        if isinstance(file_size_or_path, int):
            size_bytes = file_size_or_path
        elif file_size_or_path is not None:
            path = Path(file_size_or_path)
            if not path.exists():
                raise ValidationError(f"El archivo '{path}' no existe para validar su tamaño.")
            size_bytes = path.stat().st_size
        elif self.file_path:
            if not self.file_path.exists():
                raise ValidationError(f"El archivo '{self.file_path}' no existe para validar su tamaño.")
            size_bytes = self.file_path.stat().st_size
        else:
            raise ValidationError("No se especificó tamaño ni ruta de archivo para validar el peso.")

        if size_bytes <= 0:
            raise ValidationError("El archivo está vacío (0 bytes).")

        if size_bytes > self.max_size_bytes:
            max_mb = self.max_size_bytes / (1024 * 1024)
            current_mb = size_bytes / (1024 * 1024)
            raise ValidationError(
                f"El archivo supera el tamaño máximo permitido de {max_mb:.2f} MB (recibido: {current_mb:.2f} MB)."
            )

        return True

    def validate_midi_structure(self, file_path: Optional[Union[str, Path]] = None) -> bool:
        """
        comprueba mediante 'mido' que la estructura interna sea un MIDI válido.
        verifica cabeceras ('MThd'), pistas y que contenga al menos eventos/notas procesables.
        """
        target_path = Path(file_path) if file_path else self.file_path
        if not target_path or not target_path.exists():
            raise ValidationError(f"El archivo '{target_path}' no existe o no se especificó.")

        try:
            midi_file = mido.MidiFile(str(target_path))
            
            if not midi_file.tracks:
                raise ValidationError("El archivo MIDI no contiene pistas (tracks).")

            total_messages = sum(len(track) for track in midi_file.tracks)
            if total_messages == 0:
                raise ValidationError("El archivo MIDI no contiene eventos ni mensajes musicales.")

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Estructura MIDI inválida o corrupta: {str(e)}")

        return True

    def validate_all(self, file_path: Optional[Union[str, Path]] = None) -> Tuple[bool, Optional[str]]:
        """
        ejecuta todas las validaciones (extensión, tamaño y estructura interna).
        devuelve una tupla (es_valido, mensaje_error).
        """
        target_path = Path(file_path) if file_path else self.file_path
        try:
            self.validate_extension(target_path)
            self.validate_file_size(target_path)
            self.validate_midi_structure(target_path)
            return True, None
        except ValidationError as err:
            return False, str(err)
