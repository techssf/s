# token = "s"

# import os
# from telegram.ext import Application, CommandHandler, MessageHandler, filters


# async def start(update, context):
#     await update.message.reply_text('Olá! Sou seu Liedson. Envie uma mensagem e responderei!')

# async def respond_to_message(update, context):
#     user_message = update.message.text  # Captura a mensagem do usuário
#     print(user_message)
#     await update.message.reply_text(f'A vidae é dura zé: "{user_message}"')

# def main():
#     if not token:
#         raise ValueError("Bot token not found")
#     app = Application.builder().token(token).build()
#     app.add_handler(CommandHandler('start', start))
#     app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond_to_message))
#     app.run_polling()

# if __name__ == '__main__':
#     main()



import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from fastapi import FastAPI, Request, Response, status

token = os.getenv('TELEGRAM_TOKEN')

app = FastAPI()

telegram_app = Application.builder().token(token).build()

async def start(update: Update, context):
    await update.message.reply_text('Olá! Sou seu Liedson. Envie uma mensagem e responderei!')

async def respond_to_message(update: Update, context):
    user_message = update.message.text
    await update.message.reply_text(f'Você disse: "{user_message}"')

telegram_app.add_handler(CommandHandler('start', start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond_to_message))

@app.post('/webhook')
async def webhook(request: Request):
    update = Update.de_json(await request.json(), telegram_app.bot)
    await telegram_app.process_update(update)
    print("kkkk aqui1")
    return Response(status_code=status.HTTP_200_OK)

@app.on_event('startup')
async def startup():
    print("kkkk 77777 ===================================== 828")
    await telegram_app.bot.set_webhook(f'https://https://s-zeta-dusky.vercel.app/webhook')

@app.get('/')
async def root():
    return {'message': 'Bot está rodando!'}
