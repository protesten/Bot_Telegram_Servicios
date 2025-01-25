import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import json

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

# Función para cargar credenciales de Google
async def load_credentials():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict)
    return creds

# Función para obtener datos de Google Sheets
def get_sheet_data(creds):
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    return result.get("values", [])

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        creds = await load_credentials()
        data = get_sheet_data(creds)

        # Obtener todas las líneas únicas
        lines = sorted(set(row[0] for row in data if row))

        # Crear botones interactivos para las líneas
        buttons = [[InlineKeyboardButton(line, callback_data=f"line|{line}")] for line in lines]
        reply_markup = InlineKeyboardMarkup(buttons)

        await update.message.reply_text(
            "\u00a1Hola! Bienvenido al bot de horarios. Escribe la línea que deseas consultar o usa los menús interactivos.",
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.error(f"Error en /start: {e}")
        await update.message.reply_text("Ocurrió un error al iniciar el bot. Por favor, inténtalo más tarde.")

# Callback para manejar la selección de líneas
async def handle_line_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    try:
        creds = await load_credentials()
        data = get_sheet_data(creds)

        # Obtener línea seleccionada
        _, line = query.data.split("|")

        # Filtrar servicios disponibles para la línea seleccionada
        services = sorted(set(row[1] for row in data if row and row[0] == line))

        # Crear botones interactivos para los servicios
        buttons = [[InlineKeyboardButton(service, callback_data=f"service|{line}|{service}")] for service in services]
        reply_markup = InlineKeyboardMarkup(buttons)

        await query.edit_message_text(
            f"Línea seleccionada: {line}. Selecciona el código de servicio:",
            reply_markup=reply_markup
        )
    except Exception as e:
        logging.error(f"Error en handle_line_selection: {e}")
        await query.edit_message_text("Ocurrió un error al obtener los servicios disponibles.")

# Callback para manejar la selección de servicios
async def handle_service_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    try:
        creds = await load_credentials()
        data = get_sheet_data(creds)

        # Obtener línea y servicio seleccionados
        _, line, service = query.data.split("|")

        # Filtrar horarios para la línea y servicio seleccionados
        schedule = [row for row in data if row and row[0] == line and row[1] == service]

        if not schedule:
            await query.edit_message_text("No se encontraron horarios para esta selección.")
            return

        # Formatear y mostrar los horarios
        response = f"Línea: {line}\nServicio: {service}\n-------------\n"
        for row in schedule:
            response += f"* {row[2]} - {row[5]}\n"

        await query.edit_message_text(response)
    except Exception as e:
        logging.error(f"Error en handle_service_selection: {e}")
        await query.edit_message_text("Ocurrió un error al obtener los horarios.")

# Configuración principal del bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_line_selection, pattern="^line|"))
    app.add_handler(CallbackQueryHandler(handle_service_selection, pattern="^service|"))
    app.run_polling()
