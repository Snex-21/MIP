import logging
from pathlib import Path
from typing import Optional, Union
from pydub import AudioSegment

from config import temp_dir
from utils.file_manager import FileManager

logger = logging.getLogger(__name__)


class AudioServiceError(Exception):
    """excepción lanzada ante fallos en la compresión u optimización de audio"""
    pass


class AudioService:
    """
    servicio de compresión, conversión y optimización de archivos de audio
    utilizando FFmpeg a través de la librería pydub
    """

    def __init__(self, file_manager: Optional[FileManager] = None) -> None:
        self.file_manager = file_manager or FileManager(temp_dir)

    def compress_wav(
        self,
        wav_path: Union[str, Path],
        target_format: str = "ogg",
        bitrate: str = "128k",
        output_path: Optional[Union[str, Path]] = None,
        normalize: bool = True,
    ) -> Path:
        """
        comprime y optimiza un archivo WAV crudo a un formato ligero (.ogg o .mp3)

        :param wav_path: ruta del archivo WAV crudo a comprimir
        :param target_format: formato destino ('ogg' o 'mp3'). OGG Opus/Vorbis es el ideal para Telegram
        :param bitrate: tasa de bits para compresión ('128k', '192k', '64k', etc.)
        :param output_path: (opcional) ruta de destino para el archivo comprimido
        :param normalize: si es True, normaliza el nivel de pico de audio antes de exportar
        :return: path absoluto al archivo comprimido generado en /temp/<uuid>/
        """
        input_file = Path(wav_path).resolve()
        if not input_file.exists():
            raise AudioServiceError(f"El archivo de origen no existe: {input_file}")

        format_clean = target_format.lower().lstrip(".")
        if format_clean not in {"ogg", "mp3"}:
            raise AudioServiceError(
                f"Formato de audio '{target_format}' no soportado. Formatos permitidos: 'ogg', 'mp3'."
            )

        # determinar ubicación de salida
        if output_path:
            out_file = Path(output_path).resolve()
            out_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            # si el WAV ya está dentro de una sesión en temp/, guardar allí con la nueva extensión
            if temp_dir in input_file.parents:
                out_file = (input_file.parent / f"{input_file.stem}.{format_clean}").resolve()
            else:
                # si viene de otra ruta, crear subcarpeta UUID en /temp/
                _, session_dir = self.file_manager.create_session_dir()
                out_file = (session_dir / f"{input_file.stem}.{format_clean}").resolve()

        logger.info(
            "Iniciando compresión de audio: %s -> %s (formato: %s, bitrate: %s)",
            input_file.name,
            out_file.name,
            format_clean,
            bitrate,
        )

        try:
            # carga del audio crudo con pydub
            audio: AudioSegment = AudioSegment.from_wav(str(input_file))

            # normalización opcional del audio para sonido claro y uniforme
            if normalize:
                change_in_dbfs = -1.0 - audio.max_dBFS
                audio = audio.apply_gain(change_in_dbfs)

            # exportación con FFmpeg
            codec = "libopus" if format_clean == "ogg" else None
            parameters = ["-vbr", "on"] if format_clean == "ogg" else []

            audio.export(
                str(out_file),
                format=format_clean,
                bitrate=bitrate,
                codec=codec,
                parameters=parameters,
            )

            if not out_file.exists() or out_file.stat().st_size == 0:
                raise AudioServiceError("El archivo de audio comprimido no se generó o está vacío.")

        except Exception as e:
            if isinstance(e, AudioServiceError):
                raise
            raise AudioServiceError(f"Error durante la compresión con FFmpeg/pydub: {e}") from e

        orig_size = input_file.stat().st_size
        comp_size = out_file.stat().st_size
        reduction = (1 - (comp_size / orig_size)) * 100 if orig_size > 0 else 0

        logger.info(
            "Compresión finalizada con éxito: %s (%d bytes -> %d bytes, -%.1f%%)",
            out_file.name,
            orig_size,
            comp_size,
            reduction,
        )

        return out_file


# instancia por defecto y función de conveniencia
_default_audio_service = None


def get_default_audio_service() -> AudioService:
    global _default_audio_service
    if _default_audio_service is None:
        _default_audio_service = AudioService()
    return _default_audio_service


def compress_audio(
    wav_path: Union[str, Path],
    target_format: str = "ogg",
    bitrate: str = "128k",
    output_path: Optional[Union[str, Path]] = None,
) -> Path:
    """
    función de conveniencia para comprimir audio WAV a OGG/MP3 en /temp/<uuid>/
    """
    return get_default_audio_service().compress_wav(
        wav_path=wav_path,
        target_format=target_format,
        bitrate=bitrate,
        output_path=output_path,
    )
