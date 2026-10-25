import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
import mido

from utils.validators import MIDIValidator, ValidationError

logger = logging.getLogger(__name__)


class MIDIServiceError(Exception):
    """excepción para errores ocurridos en el servicio MIDI"""
    pass


class MIDIService:
    """
    servicio encargado de la validación técnica e inspección/lectura
    de datos estructurados de archivos MIDI (canales, instrumentos, notas, duración)
    """

    def __init__(self, validator: Optional[MIDIValidator] = None) -> None:
        self.validator = validator or MIDIValidator()

    def validate_file(self, file_path: Union[str, Path]) -> bool:
        """
        ejecuta la validación de extensión, peso y formato estructural interno
        haciendo uso del validador de utils.
        """
        path = Path(file_path)
        is_valid, error = self.validator.validate_all(path)
        if not is_valid:
            raise MIDIServiceError(f"Validación MIDI fallida: {error}")
        return True

    def read_midi_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        valida e inspecciona el archivo MIDI extrayendo metadatos clave:
        - Tipo de formato (0, 1, 2)
        - Número de pistas (tracks)
        - Ticks por negra (ticks_per_beat)
        - Duración estimada en segundos
        - Canales activos utilizados (0 al 15)
        - Conteo de notas (note_on con velocity > 0)
        - Program changes / instrumentos detectados
        """
        path = Path(file_path)
        self.validate_file(path)

        try:
            midi = mido.MidiFile(str(path))
        except Exception as e:
            raise MIDIServiceError(f"No se pudo abrir el archivo MIDI: {e}") from e

        active_channels = set()
        programs_detected: Dict[int, int] = {}  # canal -> program_number
        total_notes = 0

        for track in midi.tracks:
            for msg in track:
                if msg.type in ("note_on", "note_off"):
                    if hasattr(msg, "channel"):
                        active_channels.add(msg.channel)
                    if msg.type == "note_on" and getattr(msg, "velocity", 0) > 0:
                        total_notes += 1
                elif msg.type == "program_change":
                    channel = getattr(msg, "channel", 0)
                    program = getattr(msg, "program", 0)
                    programs_detected[channel] = program

        info: Dict[str, Any] = {
            "file_name": path.name,
            "format_type": midi.type,
            "track_count": len(midi.tracks),
            "ticks_per_beat": midi.ticks_per_beat,
            "duration_seconds": round(midi.length, 2),
            "channels": sorted(list(active_channels)),
            "channel_count": len(active_channels),
            "total_notes": total_notes,
            "programs": programs_detected,
        }

        logger.info(
            "MIDI leído con éxito: %s (Duración: %ss, Pistas: %d, Canales: %s, Notas: %d)",
            path.name,
            info["duration_seconds"],
            info["track_count"],
            info["channels"],
            info["total_notes"],
        )

        return info


# instancia por defecto y funciones de conveniencia directa
_default_service = MIDIService()


def validate_and_read_midi(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    función de conveniencia para validar y extraer la información del archivo MIDI
    """
    return _default_service.read_midi_info(file_path)
