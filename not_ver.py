import os
import asyncio
import httpx
from fastapi import FastAPI
import uvicorn
from telegram.ext import Application, CommandHandler, MessageHandler, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

async def start(update, context):
	await update.message.reply_text("Olá! Sou seu LeidaSF do Liedson 🚀. Envie uma mensagem!")

async def respond_to_message(update, context):
	user_message = update.message.text
	async with httpx.AsyncClient(timeout=60) as client:
		response = await client.post(
			"https://api.groq.com/openai/v1/chat/completions",
			headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
			json={
				"model": "mixtral-8x7b-32768",
				"messages": [
					{"role": "system", "content": "Responda de forma breve, divertida e em português."},
					{"role": "user", "content": user_message},
				],
			},
		)
	reply = response.json()["choices"][0]["message"]["content"]
	await update.message.reply_text(reply)

async def main():
	# inicia o bot como uma tarefa paralela
	bot_app = Application.builder().token(BOT_TOKEN).build()
	bot_app.add_handler(CommandHandler("start", start))
	bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond_to_message))
	asyncio.create_task(bot_app.run_polling())   # 🚀 roda em paralelo

	# inicia o servidor FastAPI
	config = uvicorn.Config(api, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
	server = uvicorn.Server(config)
	await server.serve()

api = FastAPI()

@api.get("/")
def read_root():
	return {"status": "ok", "message": "Bot e API rodando 🚀"}

if __name__ == "__main__":
	asyncio.run(main())
