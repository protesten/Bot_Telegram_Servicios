import os
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Configuración
TOKEN = "7605197922:AAFDJP7bjPCUob939Iv6LAkRolt8f6Pmwbk"
SPREADSHEET_ID = "1UWCawwwIilVsEWBQC7fFfwR7Tedbgu263fpxyWEOoiY"
RANGE_NAME = "BD!A:J"

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

def get_google_service():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict)
    service = build("sheets", "v4", credentials=creds)
    return service.spreadsheets()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await ask_line(update, context)

async def ask_line(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sheet = get_google_service()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="BD!A:A").execute()
    lines = sorted(set(row[0] for row in result.get("values", [])[1:]))

    keyboard = [[InlineKeyboardButton(line, callback_data=f"line|{line}")] for line in lines]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "¿Qué línea quieres consultar? (dejar en blanco para listar todas las líneas)",
        reply_markup=reply_markup,
    )

async def ask_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    line = query.data.split("|")[1]
    context.user_data["line"] = line

    sheet = get_google_service()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range="BD!B:B").execute()
    services = sorted(set(row[0] for row in result.get("values", [])[1:] if row[0] == line))

    keyboard = [[InlineKeyboardButton(service, callback_data=f"service|{service}")] for service in services]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Línea elegida: {line}\n¿Cuál es el código del servicio a consultar?",
        reply_markup=reply_markup,
    )

async def ask_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    service = query.data.split("|")[1]
    context.user_data["service"] = service

    keyboard = [
        [InlineKeyboardButton("TD - Todos los días", callback_data="days|TD")],
        [InlineKeyboardButton("SDF - Sábados", callback_data="days|SDF")],
        [InlineKeyboardButton("LAB - Laborables", callback_data="days|LAB")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Servicio elegido: {service}\nElige los días del servicio:",
        reply_markup=reply_markup,
    )

async def ask_season(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    days = query.data.split("|")[1]
    context.user_data["days"] = days

    keyboard = [
        [InlineKeyboardButton("IV - Todo el año", callback_data="season|IV")],
        [InlineKeyboardButton("V - Verano", callback_data="season|V")],
        [InlineKeyboardButton("I - Invierno", callback_data="season|I")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Días elegidos: {days}\n¿Qué temporada quieres los horarios?",
        reply_markup=reply_markup,
    )

async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    season = query.data.split("|")[1]
    context.user_data["season"] = season

    line = context.user_data["line"]
    service = context.user_data["service"]
    days = context.user_data["days"]

    sheet = get_google_service()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=RANGE_NAME).execute()
    values = result.get("values", [])

    # Filtrar por los datos seleccionados
    filtered = [row for row in values if row[0] == line and row[1] == service and row[7] == days and row[8] == season]

    if not filtered:
        await query.edit_message_text("No se encontraron horarios para los parámetros seleccionados.")
        return

    response = f"Línea: {line}\nServicio: {service}\nDías: {days}\nTemporada: {season}\n-------------\n"
    for row in filtered:
        response += f"* {row[2]} - {row[5]}\n"

    await query.edit_message_text(response)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(ask_service, pattern="^line\\|"))
    app.add_handler(CallbackQueryHandler(ask_days, pattern="^service\\|"))
    app.add_handler(CallbackQueryHandler(ask_season, pattern="^days\\|"))
    app.add_handler(CallbackQueryHandler(show_results, pattern="^season\\|"))

    app.run_polling()
