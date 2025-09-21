import os
import logging
import threading
from fastapi import FastAPI, Request
import uvicorn
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, Dispatcher
from groq import Groq

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_KEY)

app = FastAPI()

# Global variable for dispatcher
dispatcher = None

async def start(update, context):
    logger.info("Received /start command")
    try:
        await update.message.reply_text("Bot ativo 🚀")
        logger.info("Sent response for /start")
    except Exception as e:
        logger.error(f"Error in /start handler: {e}")

async def chat(update, context):
    user_text = update.message.text
    logger.info(f"Received message: {user_text}")
    try:
        resp = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": user_text}],
        )
        content = resp.choices[0].message.content if resp and resp.choices else "❌ Erro na resposta da API"
        await update.message.reply_text(content)
        logger.info(f"Sent response: {content[:50]}...")  # Log first 50 chars to avoid large logs
    except Exception as e:
        logger.error(f"Error in chat handler: {e}")
        await update.message.reply_text("❌ Ocorreu um erro ao processar sua mensagem.")

def setup_dispatcher(app_telegram):
    global dispatcher
    dispatcher = app_telegram.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    logger.info("Dispatcher handlers added")

@app.post("/webhook")
async def webhook(request: Request):
    global dispatcher
    if dispatcher is None:
        logger.warning("Dispatcher not initialized yet")
        return {"status": "error", "message": "Dispatcher not ready"}
    
    try:
        update_json = await request.json()
        logger.debug(f"Received webhook update: {update_json}")
        update = Update.de_json(update_json, dispatcher.bot)
        await dispatcher.process_update(update)
        logger.info("Processed webhook update successfully")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/")
def index():
    logger.info("Received GET request to root")
    return {"status": "ok"}

def run_bot():
    try:
        logger.info("Initializing Telegram application")
        app_telegram = Application.builder().token(BOT_TOKEN).build()
        setup_dispatcher(app_telegram)
        
        # Set webhook
        webhook_url = os.getenv("WEBHOOK_URL")  # Set this in Render environment variables, e.g., https://your-app.onrender.com/webhook
        if not webhook_url:
            raise ValueError("WEBHOOK_URL not set in environment variables")
        
        logger.info(f"Setting webhook to: {webhook_url}")
        app_telegram.bot.set_webhook(webhook_url)
        
        logger.info("Starting Telegram application")
        app_telegram.run_async()  # For webhook, we don't need polling; just initialize
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")

if __name__ == "__main__":
    try:
        logger.info("Starting bot in separate thread")
        threading.Thread(target=run_bot, daemon=True).start()
        
        port = int(os.getenv("PORT", 8888))
        logger.info(f"Starting Uvicorn on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        logger.critical(f"Main thread error: {e}")
