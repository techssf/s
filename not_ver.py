import os
import asyncio
import httpx
from fastapi import FastAPI
import uvicorn
from telegram.ext import Application, CommandHandler, MessageHandler, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- Handlers do Telegram ---
async def start(update, context):
	await update.message.reply_text("Olá! Sou seu LeidaSF do Liedson 🚀. Envie uma mensagem!")

async def respond_to_message(update, context):
	user_message = update.message.text
	async with httpx.AsyncClient(timeout=60) as client:
		resp = await client.post(
			"https://api.groq.com/openai/v1/chat/completions",
			headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
			json={
				"model": "mixtral-8x7b-32768",
				"messages": [
					{"role": "system", "content": "Responda de forma breve, divertida e em português."},
					{"role": "user", "content": user_message},
				],
			},
		)
	reply = resp.json()["choices"][0]["message"]["content"]
	await update.message.reply_text(reply)

# --- FastAPI ---
api = FastAPI()

@api.get("/")
def root():
	return {"status": "ok", "message": "Bot e API rodando 🚀"}

# --- Função principal ---
async def main():
	# Telegram bot
	app_bot = Application.builder().token(BOT_TOKEN).build()
	app_bot.add_handler(CommandHandler("start", start))
	app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond_to_message))

	# inicia bot sem encerrar o loop principal
	await app_bot.initialize()
	await app_bot.start()
	await app_bot.updater.start_polling()

	# inicia servidor FastAPI
	config = uvicorn.Config(api, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
	server = uvicorn.Server(config)
	await server.serve()

	# finalização graciosa (quando o uvicorn encerrar)
	await app_bot.updater.stop()
	await app_bot.stop()
	await app_bot.shutdown()

if __name__ == "__main__":
	# aqui chamamos a função assíncrona corretamente
	asyncio.run(main())
