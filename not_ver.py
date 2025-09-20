import os
import threading
import asyncio
from fastapi import FastAPI
import uvicorn
from telegram.ext import Application, CommandHandler, MessageHandler, filters
# 🔑 Tokens
BOT_TOKEN = os.getenv("BOT_TOKEN")  # render: defina no dashboard
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# --- TELEGRAM BOT HANDLERS ---
async def start(update, context):
    await update.message.reply_text("Olá! Sou seu LeidaSF do Liedson 🚀. Envie uma mensagem!")

async def respond_to_message(update, context):
    user_message = update.message.text
    print("Mensagem do usuário:", user_message)

    # Fazer chamada ao Groq
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "groq/compound",   # ou outro modelo Groq
                "messages": [
                    {"role": "system", "content": "Responda de forma breve, divertida e em português. Olá! Sou seu LeidaSF do Liedson 🚀. Envie uma mensagem!"},
                    {"role": "user", "content": user_message},
                ],
            },
        )

    data = response.json()
    reply = data["choices"][0]["message"]["content"]

    # Enviar resposta para o usuário
    await update.message.reply_text(reply)

def run_bot():
    if not BOT_TOKEN:
        raise ValueError("Bot token not found")
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

if __name__ == '__main__':
    threading.Thread(target=run_bot, daemon=True).start()
    run_http()
