import logging
import sys
from typing import Optional

# corrección de enrutamiento para Telegram DC1:
# Pyrogram tiene cableada internamente la IP 149.154.175.53 para el DC1, la cual sufre
# bloqueo o filtrado en muchos proveedores. Redirigimos a 149.154.175.50
# que es el endpoint oficial plenamente accesible.
import pyrogram.session.internals.data_center as pyrogram_dc
pyrogram_dc.DataCenter.PROD[1] = "149.154.175.50"

from pyrogram import Client, filters
from pyrogram.types import Message

from config import bot_token, api_id, api_hash
from handlers.document_handler import DocumentHandler

# configuración de logging para visibilidad en consola
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("MIPBot")


class MIPBot:
    """
    clase principal que encapsula la inicialización, configuración, registro
    de handlers y ciclo de vida de M.I.P.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        id_api: Optional[str] = None,
        hash_api: Optional[str] = None,
        document_handler: Optional[DocumentHandler] = None,
    ) -> None:
        self.bot_token = token or bot_token
        self.api_id = id_api or api_id
        self.api_hash = hash_api or api_hash

        self._validate_credentials()

        self.app = Client(
            name="mip_bot",
            api_id=int(self.api_id),
            api_hash=str(self.api_hash),
            bot_token=str(self.bot_token),
            ipv6=False,
            sleep_threshold=60,
        )

        self.document_handler = document_handler or DocumentHandler()
        self._setup_handlers()

    def _validate_credentials(self) -> None:
        """verifica que las credenciales obligatorias de Telegram estén presentes"""
        if not self.bot_token or not self.api_id or not self.api_hash:
            logger.error("Credenciales de Telegram no configuradas.")
            raise ValueError(
                "Faltan credenciales de Telegram (BOT_TOKEN, API_ID, API_HASH). "
                "Configúralas en tu archivo .env"
            )

    def _setup_handlers(self) -> None:
        """registra los comandos base y los handlers del bot"""
        # comando de bienvenida y ayuda
        @self.app.on_message(filters.command(["start"]) & filters.private)
        async def start_command(client: Client, message: Message) -> None:
            user_name = message.from_user.first_name if message.from_user else "músico"
            welcome_text = (
                f"Hola, **{user_name}**. Bienvenido a **M.I.P.** (Motor de Interpretación de Partituras).\n\n"
                "**¿Cómo funciona?**\n"
                "1. Envíame un archivo `.mid` o `.midi`.\n"
                "2. M.I.P. lo valida, interpreta los canales e instrumentos con SoundFont.\n"
                "3. En segundos recibirás una maqueta de audio reproducible directamente en este chat.\n\n"
                "*Envía tu primer archivo MIDI para comenzar*"
            )
            await message.reply_text(welcome_text)

        # registro del manejador de documentos MIDI
        self.document_handler.register(self.app)
        logger.info("Handlers y comandos registrados correctamente.")

    def run(self) -> None:
        """inicia el bot y mantiene el bucle de ejecución de Pyrogram"""
        logger.info("Iniciando M.I.P. Telegram Bot...")
        try:
            self.app.run()
        except KeyboardInterrupt:
            logger.info("Bot detenido manualmente por el usuario.")
        except Exception as e:
            logger.critical("Error fatal al ejecutar el bot: %s", e)
            sys.exit(1)


if __name__ == "__main__":
    bot = MIPBot()
    bot.run()
