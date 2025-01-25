import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import json

TOKEN = "7605197922:AAFDJP7bjPCUob939Iv6LAkRolt8f6Pmwbk"
SPREADSHEET_ID = "1UWCawwwIilVsEWBQC7fFfwR7Tedbgu263fpxyWEOoiY"
RANGE_NAME = "BD!A:J"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("¡Hola! El bot está funcionando.")


async def test_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Verificar si las credenciales se cargan correctamente
        creds_json = os.environ.get("GOOGLE_CREDENTIALS")
        if not creds_json:
            raise ValueError("La variable GOOGLE_CREDENTIALS no está configurada.")
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict)
        await update.message.reply_text("Las credenciales se cargaron correctamente.")
    except Exception as e:
        await update.message.reply_text(f"Error al cargar credenciales: {e}")


async def get_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        creds_json = os.environ.get("GOOGLE_CREDENTIALS")
        if not creds_json:
            raise ValueError("La variable GOOGLE_CREDENTIALS no está configurada.")
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict)

        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()

        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get("values", [])

        if not values:
            await update.message.reply_text("No se encontraron datos.")
            return

        response = "Datos obtenidos:\n"
        for row in values[:5]:
            response += " - ".join(row) + "\n"

        await update.message.reply_text(response)
    except ValueError as ve:
        logging.error(f"Error en credenciales: {ve}")
        await update.message.reply_text("Ocurrió un error con las credenciales.")
    except Exception as e:
        logging.error(f"Error al obtener datos: {e}")
        await update.message.reply_text("Ocurrió un error al obtener los datos.")


if __name__ == "__main__":
    os.environ["GOOGLE_CREDENTIALS"] = os.getenv("GOOGLE_CREDENTIALS")  # Forzar lectura
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_credentials", test_credentials))
    app.add_handler(CommandHandler("datos", get_data))
    app.run_polling()
