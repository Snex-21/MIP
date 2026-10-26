import asyncio
import logging
from pathlib import Path
from typing import Optional
from pyrogram import Client, filters
from pyrogram.types import Message

from utils.file_manager import FileManager
from utils.validators import MIDIValidator, ValidationError
from services.midi_service import MIDIService, MIDIServiceError
from services.synth_service import SynthService, SynthServiceError
from services.audio_service import AudioService, AudioServiceError

logger = logging.getLogger(__name__)


class DocumentHandler:
    """
    controlador encargado de gestionar la recepción,
    procesamiento y entrega de archivos musicales enviados al bot
    """

    def __init__(
        self,
        file_manager: Optional[FileManager] = None,
        validator: Optional[MIDIValidator] = None,
        midi_service: Optional[MIDIService] = None,
        synth_service: Optional[SynthService] = None,
        audio_service: Optional[AudioService] = None,
    ) -> None:
        self.file_manager = file_manager or FileManager()
        self.validator = validator or MIDIValidator()
        self.midi_service = midi_service or MIDIService(validator=self.validator)
        self.synth_service = synth_service or SynthService(file_manager=self.file_manager)
        self.audio_service = audio_service or AudioService(file_manager=self.file_manager)

    async def handle_document(self, client: Client, message: Message) -> None:
        """
        intercepta y ejecuta el pipeline completo de procesamiento para un archivo MIDI recibido
        """
        document = message.document
        if not document:
            return

        file_name = document.file_name or "archivo.mid"
        session_id = None
        status_msg = None

        try:
            # 1. validación preliminar rápida (extensión y límite de peso)
            try:
                self.validator.validate_extension(file_name)
                self.validator.validate_file_size(document.file_size)
            except ValidationError as err:
                await message.reply_text(f" **Archivo rechazado:** {str(err)}")
                return

            # 2. creación de directorio temporal de sesión con UUID4
            session_id, session_dir = self.file_manager.create_session_dir()
            download_path = session_dir / file_name

            status_msg = await message.reply_text("Descargando archivo MIDI...")

            # 3. descarga del archivo
            await client.download_media(message=message, file_name=str(download_path))

            # 4. inspección y validación estructural del MIDI
            await status_msg.edit_text("Validando estructura de la partitura MIDI...")
            loop = asyncio.get_running_loop()
            midi_info = await loop.run_in_executor(
                None,
                self.midi_service.read_midi_info,
                download_path,
            )

            # 5. síntesis sonora a WAV con FluidSynth
            await status_msg.edit_text("Interpretando notas y sintetizando instrumentos...")
            wav_path = await loop.run_in_executor(
                None,
                self.synth_service.synthesize_to_wav,
                download_path,
            )

            # 6. compresión y optimización a OGG (Opus) con FFmpeg / pydub
            await status_msg.edit_text("Comprimiendo y optimizando audio...")
            audio_path = await loop.run_in_executor(
                None,
                self.audio_service.compress_wav,
                wav_path,
                "ogg",
            )

            # 7. entrega de la maqueta de audio
            await status_msg.edit_text("Enviando maqueta de audio...")
            caption = (
                f"**Maqueta generada con éxito**\n\n"
                f"**Archivo:** `{file_name}`\n"
                f"**Duración:** `{midi_info.get('duration_seconds', 0)}s`\n"
                f"**Pistas:** `{midi_info.get('track_count', 0)}` | **Notas:** `{midi_info.get('total_notes', 0)}`\n"
                f"**M.I.P.** - Motor de Interpretación de Partituras"
            )

            await client.send_voice(
                chat_id=message.chat.id,
                voice=str(audio_path),
                caption=caption,
                duration=int(midi_info.get("duration_seconds", 0)),
                reply_to_message_id=message.id,
            )

            await status_msg.delete()

        except (ValidationError, MIDIServiceError) as err:
            logger.warning("Error de validación MIDI: %s", err)
            error_text = f"**Error en el archivo MIDI:** {str(err)}"
            if status_msg:
                await status_msg.edit_text(error_text)
            else:
                await message.reply_text(error_text)

        except (SynthServiceError, AudioServiceError) as err:
            logger.error("Error durante el procesamiento sonoro: %s", err)
            error_text = f"**Error al procesar el audio:** {str(err)}"
            if status_msg:
                await status_msg.edit_text(error_text)
            else:
                await message.reply_text(error_text)

        except Exception as err:
            logger.exception("Error inesperado en DocumentHandler: %s", err)
            error_text = "Ocurrió un error inesperado al procesar tu archivo. Por favor, intenta de nuevo."
            if status_msg:
                await status_msg.edit_text(error_text)
            else:
                await message.reply_text(error_text)

        finally:
            # 8. limpieza completa de sesión y archivos temporales
            if session_id:
                logger.info("Ejecutando limpieza de la sesión %s", session_id)
                self.file_manager.cleanup_session(session_id)

    def register(self, app: Client) -> None:
        """
        registra el handler en la instancia de Pyrogram Client
        """
        app.on_message(filters.document & filters.private)(self.handle_document)


# instancia por defecto y función de registro rápida
_default_document_handler = DocumentHandler()


def register_document_handler(app: Client) -> None:
    """
    función de registro para conectar el handler a Pyrogram
    """
    _default_document_handler.register(app)
