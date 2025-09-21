import os
import threading
from fastapi import FastAPI
import uvicorn
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from groq import Groq

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

groq_client = Groq(api_key=GROQ_API_KEY)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	await update.message.reply_text(
		"Olá! Sou seu LeidaSF do Liedson 🚀. Envie uma mensagem!"
	)

async def respond_to_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
	user_message = update.message.text
	try:
		# >>> Usa o MESMO modelo anterior <<<
		resp = groq_client.chat.completions.create(
			model="groq/compound",  # mesmo modelo que você usava
			messages=[
				{"role": "system",
				 "content": "Responda de forma breve, divertida e em português. "
				            "Olá! Sou seu LeidaSF do Liedson 🚀. Envie uma mensagem!"},
				{"role": "user", "content": user_message},
			],
		)

		if not resp.choices:
			await update.message.reply_text("⚠️ Nenhuma resposta recebida da IA.")
			return

		reply = resp.choices[0].message.content
		await update.message.reply_text(reply)

	except Exception as e:
		print("Erro na Groq:", e)
		await update.message.reply_text("⚠️ Erro ao processar a resposta da IA.")

def run_bot():
	if not BOT_TOKEN:
		raise ValueError("BOT_TOKEN não definido.")
	app = Application.builder().token(BOT_TOKEN).build()
	app.add_handler(CommandHandler("start", start))
	app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond_to_message))
	app.run_polling()

api = FastAPI()

@api.get("/")
def read_root():
	return {"status": "ok", "message": "Bot está rodando no Render 🚀"}

def run_http():
	port = int(os.getenv("PORT", 8000))
	uvicorn.run(api, host="0.0.0.0", port=port)

if __name__ == "__main__":
	threading.Thread(target=run_bot, daemon=True).start()
	run_http()
