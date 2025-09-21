import os
import threading
from fastapi import FastAPI
import uvicorn
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from groq import Groq

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_KEY)

app = FastAPI()

@app.get("/")
def index():
	return {"status": "ok"}

async def start(update, context):
	await update.message.reply_text("Bot ativo 🚀")

async def chat(update, context):
	user_text = update.message.text
	resp = groq_client.chat.completions.create(
		model="mixtral-8x7b-32768",
		messages=[{"role": "user", "content": user_text}],
	)
	content = resp.choices[0].message.content if resp and resp.choices else "❌ Erro na resposta da API"
	await update.message.reply_text(content)

def run_bot():
	app_telegram = (
		Application.builder()
		.token(BOT_TOKEN)
		.build()
	)
	app_telegram.add_handler(CommandHandler("start", start))
	app_telegram.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
	app_telegram.run_polling()

if __name__ == "__main__":
	threading.Thread(target=run_bot, daemon=True).start()
	uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8888)))
