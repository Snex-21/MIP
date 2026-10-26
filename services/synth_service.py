import logging
import subprocess
from pathlib import Path
from typing import Optional, Union, Tuple

from config import soundfont_path as default_sf2, fluidsynth_bin as default_fluidsynth, temp_dir
from utils.file_manager import FileManager

logger = logging.getLogger(__name__)


class SynthServiceError(Exception):
    """excepción lanzada cuando ocurre un error durante la síntesis de audio"""
    pass


class SynthService:
    """
    servicio encargado de la sintesis de archivos MIDI a audio crudo (.wav)
    utilizando FluidSynth y un archivo SoundFont (.sf2).
    """

    def __init__(
        self,
        soundfont_path: Optional[Union[str, Path]] = None,
        fluidsynth_bin: Optional[str] = None,
        sample_rate: int = 44100,
        file_manager: Optional[FileManager] = None,
    ) -> None:
        self.soundfont_path = Path(soundfont_path).resolve() if soundfont_path else default_sf2
        self.fluidsynth_bin = fluidsynth_bin or default_fluidsynth
        self.sample_rate = sample_rate
        self.file_manager = file_manager or FileManager(temp_dir)

        self._validate_dependencies()

    def _validate_dependencies(self) -> None:
        """verifica que el archivo SoundFont exista en el sistema"""
        if not self.soundfont_path or not self.soundfont_path.exists():
            raise SynthServiceError(
                f"No se encontró el archivo SoundFont en '{self.soundfont_path}'. "
                "Revisa la variable SOUNDFONT_PATH en tu archivo .env."
            )

    def synthesize_to_wav(
        self,
        midi_path: Union[str, Path],
        output_wav_path: Optional[Union[str, Path]] = None,
        gain: float = 0.8,
    ) -> Path:
        """
        sintetiza un archivo MIDI a WAV sin reproducirlo en altavoces (Fast Render)
        
        si no se provee `output_wav_path`, se genera automáticamente dentro de una subcarpeta
        de sesión única en /temp/<uuid>/ usando FileManager.

        :param midi_path: ruta del archivo .mid de entrada
        :param output_wav_path: (opcional) Ruta destino para el .wav
        :param gain: ganancia de volumen (0.8 por defecto)
        :return: path absoluto al archivo .wav generado en /temp/
        """
        midi_file = Path(midi_path).resolve()
        if not midi_file.exists():
            raise SynthServiceError(f"El archivo MIDI no existe: {midi_file}")

        if output_wav_path:
            wav_file = Path(output_wav_path).resolve()
            wav_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            # si el MIDI ya está en un subdirectorio de temp, se genera allí;
            # si viene de otra ubicación externa, crea una sesión temporal con UUID
            if temp_dir in midi_file.parents:
                wav_file = (midi_file.parent / f"{midi_file.stem}.wav").resolve()
            else:
                _, session_dir = self.file_manager.create_session_dir()
                wav_file = (session_dir / f"{midi_file.stem}.wav").resolve()

        cmd = [
            str(self.fluidsynth_bin),
            "-ni",
            "-g", str(gain),
            "-r", str(self.sample_rate),
            "-F", str(wav_file),
            str(self.soundfont_path),
            str(midi_file),
        ]

        logger.info("Iniciando síntesis FluidSynth: %s -> %s", midi_file.name, wav_file.name)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                raise SynthServiceError(
                    f"Error de FluidSynth (código {result.returncode}): {result.stderr.strip()}"
                )

            if not wav_file.exists() or wav_file.stat().st_size == 0:
                raise SynthServiceError("FluidSynth finalizó pero el archivo .wav no se generó o está vacío.")

        except FileNotFoundError as err:
            raise SynthServiceError(
                f"Ejecutable de FluidSynth '{self.fluidsynth_bin}' no disponible en el sistema. "
                "Verifica la variable FLUIDSYNTH_BIN en tu archivo .env."
            ) from err
        except Exception as err:
            if isinstance(err, SynthServiceError):
                raise
            raise SynthServiceError(f"Fallo inesperado al sintetizar MIDI: {err}") from err

        logger.info("Síntesis finalizada con éxito: %s (%d bytes)", wav_file.name, wav_file.stat().st_size)
        return wav_file


# Instancia por defecto y función de conveniencia
_default_synth = None


def get_default_synth() -> SynthService:
    global _default_synth
    if _default_synth is None:
        _default_synth = SynthService()
    return _default_synth


def synthesize(midi_path: Union[str, Path], output_wav_path: Optional[Union[str, Path]] = None) -> Path:
    """
    función de conveniencia para sintetizar un archivo MIDI a WAV (por defecto en /temp/)
    """
    return get_default_synth().synthesize_to_wav(midi_path, output_wav_path)
