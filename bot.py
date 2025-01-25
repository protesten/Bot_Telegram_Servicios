import os
import logging
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Token del bot de Telegram
TOKEN = "7605197922:AAFDJP7bjPCUob939Iv6LAkRolt8f6Pmwbk"

# ID y rango de la hoja de Google Sheets
SPREADSHEET_ID = "1UWCawwwIilVsEWBQC7fFfwR7Tedbgu263fpxyWEOoiY"
RANGE_NAME = "BD!A:J"

# Configuración básica de logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("¡Hola! El bot está funcionando.")

# Comando para verificar las credenciales
async def test_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        creds_json = os.environ.get("GOOGLE_CREDENTIALS")
        if not creds_json:
            raise ValueError("La variable GOOGLE_CREDENTIALS no está configurada.")
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict)
        await update.message.reply_text("Las credenciales se cargaron correctamente.")
    except Exception as e:
        await update.message.reply_text(f"Error al cargar credenciales: {e}")

# Comando para obtener datos de la hoja de cálculo
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
            await update.message.reply_text("No se encontraron datos en el rango especificado.")
            return

        response = "Datos obtenidos:\n"
        for row in values[:5]:  # Limitar a las primeras 5 filas
            response += " - ".join(row) + "\n"

        await update.message.reply_text(response)
    except Exception as e:
        error_message = f"Error al obtener datos: {e}"
        logging.error(error_message)
        await update.message.reply_text(error_message)

# Comando para depurar las variables de entorno
async def debug_env(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        google_credentials = os.environ.get("GOOGLE_CREDENTIALS")
        if not google_credentials:
            await update.message.reply_text("La variable GOOGLE_CREDENTIALS no está configurada.")
            return
        await update.message.reply_text("GOOGLE_CREDENTIALS detectada correctamente.")
    except Exception as e:
        await update.message.reply_text(f"Error al depurar variables de entorno: {e}")

# Configuración principal del bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_credentials", test_credentials))
    app.add_handler(CommandHandler("datos", get_data))
    app.add_handler(CommandHandler("debug_env", debug_env))
    app.run_polling(drop_pending_updates=True)
