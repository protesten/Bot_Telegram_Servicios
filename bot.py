import os
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# Configuración básica
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Variables globales
TOKEN = "7605197922:AAFDJP7bjPCUob939Iv6LAkRolt8f6Pmwbk"
SPREADSHEET_ID = "1UWCawwwIilVsEWBQC7fFfwR7Tedbgu263fpxyWEOoiY"

# Funciones auxiliares
def get_google_sheets_service():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict)
    service = build("sheets", "v4", credentials=creds)
    return service

def obtener_datos_sheets(range_name):
    try:
        service = get_google_sheets_service()
        sheet = service.spreadsheets()
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
        values = result.get("values", [])
        return values
    except Exception as e:
        logging.error(f"Error al obtener datos de Sheets: {e}")
        return []

# Funciones del bot
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        # Obtener líneas únicas desde Google Sheets
        valores = obtener_datos_sheets("BD!A:A")
        lineas = sorted(set(row[0] for row in valores if row))  # Evitar duplicados y valores vacíos

        # Crear botones dinámicos para las líneas
        keyboard = [[InlineKeyboardButton(linea, callback_data=f"linea_{linea}")] for linea in lineas]

        # Enviar el mensaje con el teclado dinámico
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "¿Qué línea quieres consultar? (dejar en blanco para listar todas las líneas)",
            reply_markup=reply_markup,
        )

    except Exception as e:
        logging.error(f"Error al iniciar el bot: {e}")
        await update.message.reply_text("Hubo un error al iniciar el bot. Inténtalo más tarde.")

async def linea_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Obtener línea seleccionada
    data = query.data
    if data.startswith("linea_"):
        linea = data.split("_")[1]
        servicios = obtener_datos_sheets(f"BD!B:B")  # Obtener todos los servicios de la línea
        servicios_filtrados = sorted(set(row[0] for row in servicios if row and row[0].startswith(linea)))

        # Crear botones para servicios
        keyboard = [[InlineKeyboardButton(servicio, callback_data=f"servicio_{servicio}")] for servicio in servicios_filtrados]

        # Responder con el siguiente paso
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"Línea elegida: {linea}\n¿Cuál es el código del servicio a consultar?",
            reply_markup=reply_markup,
        )

async def servicio_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Obtener servicio seleccionado
    data = query.data
    if data.startswith("servicio_"):
        servicio = data.split("_")[1]

        # Crear opciones para días
        keyboard = [
            [InlineKeyboardButton("TD - Todos los días", callback_data=f"dias_TD_{servicio}"),
             InlineKeyboardButton("LAB - Laborables", callback_data=f"dias_LAB_{servicio}"),
             InlineKeyboardButton("SDF - Sábados", callback_data=f"dias_SDF_{servicio}")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"Servicio elegido: {servicio}\nElige los días del servicio:",
            reply_markup=reply_markup,
        )

async def dias_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Obtener días seleccionados
    data = query.data
    if data.startswith("dias_"):
        _, dias, servicio = data.split("_")

        # Crear opciones para temporada
        keyboard = [
            [InlineKeyboardButton("IV - Todo el año", callback_data=f"temporada_IV_{servicio}_{dias}"),
             InlineKeyboardButton("V - Verano", callback_data=f"temporada_V_{servicio}_{dias}"),
             InlineKeyboardButton("I - Invierno", callback_data=f"temporada_I_{servicio}_{dias}")]
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"Días seleccionados: {dias}\nElige la temporada:",
            reply_markup=reply_markup,
        )

async def temporada_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Obtener temporada seleccionada
    data = query.data
    if data.startswith("temporada_"):
        _, temporada, servicio, dias = data.split("_")

        # Obtener horarios desde Google Sheets
        valores = obtener_datos_sheets("BD!A:J")
        horarios = [row for row in valores if row and row[0] == servicio and row[8] == dias and row[9] == temporada]

        # Construir respuesta
        if horarios:
            respuesta = f"Horarios para el servicio {servicio}, días {dias}, temporada {temporada}:\n"
            for horario in horarios:
                respuesta += f"* {horario[2]} - {horario[5]}\n"
        else:
            respuesta = f"No se encontraron horarios para el servicio {servicio}, días {dias}, temporada {temporada}."

        await query.edit_message_text(respuesta)

# Configuración principal del bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(linea_handler, pattern="^linea_"))
    app.add_handler(CallbackQueryHandler(servicio_handler, pattern="^servicio_"))
    app.add_handler(CallbackQueryHandler(dias_handler, pattern="^dias_"))
    app.add_handler(CallbackQueryHandler(temporada_handler, pattern="^temporada_"))
    app.run_polling()
