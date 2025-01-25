import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import json

# Configuración básica del bot
TOKEN = "7605197922:AAFDJP7bjPCUob939Iv6LAkRolt8f6Pmwbk"
SPREADSHEET_ID = "1UWCawwwIilVsEWBQC7fFfwR7Tedbgu263fpxyWEOoiY"
RANGE_NAME = "BD!A:J"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

def get_google_sheet_data():
    """Obtiene los datos de Google Sheets."""
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict)
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    return result.get("values", [])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("¡Hola! Bienvenido al bot de horarios. Escribe la línea que deseas consultar o usa los menús interactivos.")

async def get_lineas(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = get_google_sheet_data()
    lineas = sorted(set(row[0] for row in data if row))  # Extraer líneas únicas
    buttons = [InlineKeyboardButton(linea, callback_data=f"linea:{linea}") for linea in lineas]
    keyboard = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]  # Agrupar en filas de 3
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Selecciona una línea:", reply_markup=reply_markup)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    data = query.data.split(":")
    if data[0] == "linea":
        linea = data[1]
        # Filtrar servicios de la línea seleccionada
        all_data = get_google_sheet_data()
        servicios = sorted(set(row[1] for row in all_data if row and row[0] == linea))
        buttons = [InlineKeyboardButton(servicio, callback_data=f"servicio:{linea}:{servicio}") for servicio in servicios]
        keyboard = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"Línea seleccionada: {linea}\nSelecciona un servicio:", reply_markup=reply_markup)

    elif data[0] == "servicio":
        linea, servicio = data[1], data[2]
        await show_horarios(query, linea, servicio)

async def show_horarios(query, linea, servicio):
    """Muestra los horarios según la línea y el servicio."""
    all_data = get_google_sheet_data()
    horarios = [row for row in all_data if row[0] == linea and row[1] == servicio]

    if not horarios:
        await query.edit_message_text(f"No se encontraron datos para la línea {linea}, servicio {servicio}. Verifica los datos e inténtalo nuevamente.")
        return

    response = f"Línea: {linea}\nServicio: {servicio}\n\n"
    for row in horarios:
        response += f"* {row[2]} - {row[5]} - {row[6]}\n"

    # Agregar notas específicas y generales al final
    notas_especificas = sorted(set((row[4], row[5]) for row in horarios if row[4]))
    notas_generales = sorted(set(row[3] for row in horarios if row[3]))

    if notas_especificas:
        response += "\nNotas específicas:\n"
        for nota, descripcion in notas_especificas:
            response += f"{nota} - {descripcion}\n"

    if notas_generales:
        response += "\nNotas generales:\n"
        for nota in notas_generales:
            response += f"{nota}\n"

    await query.edit_message_text(response)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("lineas", get_lineas))
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    app.run_polling()
