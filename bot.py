import os
import logging
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Configuración del bot
TOKEN = "7605197922:AAFDJP7bjPCUob939Iv6LAkRolt8f6Pmwbk"
SPREADSHEET_ID = "1UWCawwwIilVsEWBQC7fFfwR7Tedbgu263fpxyWEOoiY"
RANGE_NAME = "BD!A:J"

# Configuración de logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Función para cargar las credenciales de Google
def load_credentials():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not creds_json:
        raise ValueError("La variable GOOGLE_CREDENTIALS no está configurada correctamente.")
    creds_dict = json.loads(creds_json)
    return Credentials.from_service_account_info(creds_dict)

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("\u00a1Hola! El bot est\u00e1 funcionando correctamente.")

# Comando /test_credentials
async def test_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        creds = load_credentials()
        await update.message.reply_text("Las credenciales se cargaron correctamente.")
    except Exception as e:
        logging.error(f"Error al cargar credenciales: {e}")
        await update.message.reply_text(f"Error al cargar credenciales: {e}")

# Comando /datos
async def get_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        creds = load_credentials()
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()

        # Obtener los datos de la hoja
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
        values = result.get("values", [])

        if not values:
            await update.message.reply_text("No se encontraron datos en la hoja especificada.")
            return

        # Formatear los datos para la respuesta
        response = "\u00a1Datos obtenidos!\n\n"
        for row in values[:5]:  # Limitar a las primeras 5 filas
            response += " | ".join(row) + "\n"

        await update.message.reply_text(response)

    except Exception as e:
        logging.error(f"Error al obtener datos: {e}")
        await update.message.reply_text(f"Error al obtener datos: {e}")

# Configuración principal del bot
if __name__ == "__main__":
    # Crear la aplicación del bot
    app = ApplicationBuilder().token(TOKEN).build()

    # Registrar comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test_credentials", test_credentials))
    app.add_handler(CommandHandler("datos", get_data))

    # Ejecutar el bot
    app.run_polling()
