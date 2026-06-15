import os
from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters, ConversationHandler
)

from db import (
    init_db, get_user, create_user, update_interactions,
    get_balance, get_transactions, save_loan_simulation
)
from logic import calculate_loan, format_currency
from ai import detect_intent, get_ai_response

# Cargar variables del entorno
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()

# Estados para el flujo de conversación del préstamo
MONTO, PLAZO = range(2)

# Comando /start


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id)

    if not user:
        nombre = update.effective_user.first_name
        create_user(user_id, nombre)
        await update.message.reply_text(f"👋 ¡Bienvenido {nombre}! Para comenzar, necesitas autenticarte.")
        await update.message.reply_text("🔒 Ingresá tu PIN para acceder a tu cuenta:")
        context.user_data["autenticado"] = False
    else:
        if context.user_data.get("autenticado"):
            keyboard = [['/saldo', '/movimientos'], ['/prestamo', '/ayuda']]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            await update.message.reply_text(
                f"👋 ¡Hola de nuevo {user[1]}! ¿En qué puedo ayudarte hoy?",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text("🔒 Ingresá tu PIN para acceder a tu cuenta:")

# Verificación del PIN


async def verificar_pin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    mensaje = update.message.text.strip()

    if context.user_data.get("autenticado"):
        return await procesar_mensaje(update, context)

    PIN_CORRECTO = "1234"

    if mensaje == PIN_CORRECTO:
        context.user_data["autenticado"] = True
        update_interactions(user_id)

        keyboard = [['/saldo', '/movimientos'], ['/prestamo', '/ayuda']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

        await update.message.reply_text("🔓 ¡Autenticación exitosa!", reply_markup=reply_markup)

        await update.message.reply_text(
            "💡 Podés usar los siguientes comandos:\n"
            "- /start - Iniciar o reiniciar el bot\n"
            "- /saldo - Consultar tu saldo actual\n"
            "- /movimientos - Mostrar tus últimos movimientos\n"
            "- /prestamo - Simular un préstamo\n"
            "- /cancelar - Cancelar el flujo de la simulación de préstamo\n"
            "- /ayuda - Mostrar este menú y ejemplos de preguntas"
        )

        await update.message.reply_text(
            "🧠 También podés escribirme preguntas como:\n"
            "- ¿Cuánto tengo en mi cuenta?\n"
            "- Mostrame los últimos movimientos\n"
            "- Necesito un préstamo\n"
            "- ¿Cuánto pagaría si pido 100.000 en 24 cuotas?\n"
            "- ¿Qué tarjetas ofrecen?\n"
            "- ¿Conviene un plazo fijo?\n"
            "- ¿Cuál es la tasa para préstamos personales?"
        )
    else:
        await update.message.reply_text("❌ PIN incorrecto. Probá de nuevo.")


# Consulta de saldo

async def consultar_saldo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.user_data.get("autenticado"):
        await update.message.reply_text("🔒 Necesitás autenticarte primero con /start.")
        return

    update_interactions(user_id)
    saldo = get_balance(user_id)
    await update.message.reply_text(f"💰 Tu saldo actual es: {saldo}")

# Consulta de movimientos


async def consultar_movimientos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.user_data.get("autenticado"):
        await update.message.reply_text("🔒 Necesitás autenticarte primero con /start.")
        return

    update_interactions(user_id)
    movimientos = get_transactions(user_id)

    if movimientos:
        mensaje = "📄 Tus últimos movimientos:\n" + "\n".join(movimientos)
    else:
        mensaje = "📭 No tenés movimientos recientes."

    await update.message.reply_text(mensaje)

# Iniciar simulación de préstamo


async def iniciar_prestamo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.user_data.get("autenticado"):
        await update.message.reply_text("🔒 Necesitás autenticarte primero con /start.")
        return

    update_interactions(user_id)
    await update.message.reply_text("💵 Ingresá el monto que necesitás (solo números):")
    return MONTO

# Procesar monto


async def procesar_monto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip().replace(".", "").replace(",", "")

    try:
        monto = float(texto)
        if monto <= 0:
            await update.message.reply_text("❌ El monto debe ser mayor a 0. Ingresá otro valor:")
            return MONTO
        if monto > 5000000:
            await update.message.reply_text("❌ El monto máximo es de $5.000.000. Ingresá un valor menor:")
            return MONTO

        context.user_data["monto_prestamo"] = monto
        await update.message.reply_text(f"✅ Monto: {format_currency(monto)}\n\n📆 Ahora, ingresá el plazo en meses (1-60):")
        return PLAZO

    except ValueError:
        await update.message.reply_text("❌ Ingresá solo números. Por ejemplo: 100000")
        return MONTO

# Procesar plazo


async def procesar_plazo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    texto = update.message.text.strip()

    try:
        plazo = int(texto)
        if plazo <= 0 or plazo > 60:
            await update.message.reply_text("❌ El plazo debe ser entre 1 y 60 meses. Ingresá otro valor:")
            return PLAZO

        monto = context.user_data.get("monto_prestamo")
        user = get_user(user_id)
        interacciones = user[4] if user else 0

        resultado = calculate_loan(monto, plazo, interacciones)

        save_loan_simulation(
            user_id,
            resultado["monto"],
            resultado["plazo"],
            resultado["tasa_anual"],
            resultado["cuota_mensual"],
            resultado["total"]
        )

        mensaje = (
            f"📊 *Simulación de préstamo*\n\n"
            f"💵 Monto solicitado: {format_currency(resultado['monto'])}\n"
            f"📆 Plazo: {resultado['plazo']} meses\n"
            f"📈 Tasa anual: {resultado['tasa_anual']}%\n"
            f"📈 Tasa mensual: {resultado['tasa_mensual']}%\n"
            f"💰 Cuota mensual: {format_currency(resultado['cuota_mensual'])}\n"
            f"💰 Total a pagar: {format_currency(resultado['total'])}"
        )

        await update.message.reply_text(mensaje)
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("❌ Ingresá solo números. Por ejemplo: 12")
        return PLAZO

# Cancelar conversación


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operación cancelada.")
    return ConversationHandler.END

# Comando /ayuda


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "🏦 *Bot Bancario - Comandos disponibles*\n\n"
        "/start - Iniciar o reiniciar el bot\n"
        "/saldo - Consultar tu saldo actual\n"
        "/movimientos - Ver tus últimos movimientos\n"
        "/prestamo - Simular un préstamo personal\n"
        "/ayuda - Mostrar este mensaje\n\n"
        "También podés hacerme preguntas como:\n"
        "- ¿Cuánto tengo en mi cuenta?\n"
        "- Necesito un préstamo\n"
        "- ¿Qué tarjetas ofrecen?\n"
        "- ¿Conviene un plazo fijo?"
    )
    await update.message.reply_text(mensaje)

# Procesar mensajes


async def procesar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    mensaje = update.message.text

    if not context.user_data.get("autenticado"):
        return await verificar_pin(update, context)

    update_interactions(user_id)
    intent = await detect_intent(mensaje)

    if intent == "saldo":
        return await consultar_saldo(update, context)
    elif intent == "movimientos":
        return await consultar_movimientos(update, context)
    elif intent == "prestamo":
        await update.message.reply_text("💵 Para simular un préstamo, vamos a necesitar algunos datos.")
        return await iniciar_prestamo(update, context)
    else:
        respuesta = await get_ai_response(mensaje)
        await update.message.reply_text(respuesta)

# Función principal


def main():
    if not TELEGRAM_TOKEN:
        raise SystemExit(
            "TELEGRAM_TOKEN is not configured. Set it in .env or as an environment variable before starting the bot."
        )

    if not init_db():
        raise SystemExit("Could not initialize the SQLite database.")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    prestamo_handler = ConversationHandler(
        entry_points=[CommandHandler("prestamo", iniciar_prestamo)],
        states={
            MONTO: [MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_monto)],
            PLAZO: [MessageHandler(
                filters.TEXT & ~filters.COMMAND, procesar_plazo)]
        },
        fallbacks=[CommandHandler("cancelar", cancelar)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("saldo", consultar_saldo))
    app.add_handler(CommandHandler("movimientos", consultar_movimientos))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(prestamo_handler)
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, procesar_mensaje))

    print("✅ Bot bancario iniciado! Presiona Ctrl+C para detener.")
    app.run_polling()


if __name__ == "__main__":
    main()
