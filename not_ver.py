token = "8365512729:AAEB3mcMebk2_wi3mezaApT21DVHoQe8_oM"

import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters


async def start(update, context):
    await update.message.reply_text('Olá! Sou seu LeidaSF. Envie uma mensagem e responderei!')

async def respond_to_message(update, context):
    user_message = update.message.text  # Captura a mensagem do usuário
    print(user_message)
    await update.message.reply_text(f'A vidae é dura zé: "{user_message}"')

def main():
    if not token:
        raise ValueError("Bot token not found")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond_to_message))
    app.run_polling()

if __name__ == '__main__':
    main()
