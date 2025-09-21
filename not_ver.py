import os, asyncio
from fastapi import FastAPI
import uvicorn
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from groq import Groq

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)

app_http = FastAPI()

@app_http.get("/")
async def root():
	return {"status": "ok"}

async def start(update, context):
	await update.message.reply_text("Olá! Bot rodando 🚀")

async def echo(update, context):
	msg = update.message.text
	resp = groq_client.chat.completions.create(
		model="groq/compound",
		messages=[{"role":"user","content":msg}],
	)
	await update.message.reply_text(resp.choices[0].message.content)

async def main():
	# Telegram bot
	bot_app = (
		Application.builder()
		.token(BOT_TOKEN)
		.build()
	)
	bot_app.add_handler(CommandHandler("start", start))
	bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

	# Rodar bot e HTTP juntos
	await asyncio.gather(
		bot_app.run_polling(close_loop=False),
		uvicorn.Server(
			uvicorn.Config(app_http, host="0.0.0.0",
			               port=int(os.getenv("PORT", 8000)))
		).serve()
	)

if __name__ == "__main__":
	asyncio.run(main())
