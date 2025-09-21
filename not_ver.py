import os
import logging
from fastapi import FastAPI, Request
import uvicorn
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from groq import Groq

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Output to console
        logging.FileHandler('bot.log')  # Output to a file for persistence
    ]
)
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://your-app.onrender.com/webhook
PORT = int(os.getenv("PORT", 8888))

# Initialize Groq client
if not GROQ_KEY:
    logger.critical("GROQ_API_KEY not set in environment variables")
    raise ValueError("GROQ_API_KEY is required")
groq_client = Groq(api_key=GROQ_KEY)

# Initialize FastAPI app
app = FastAPI()

# Global variable for Telegram application
telegram_app = None

async def start(update: Update, context):
    logger.info(f"Received /start command from user {update.effective_user.id}")
    try:
        await update.message.reply_text("Bot ativo 🚀")
        logger.info("Sent response for /start")
    except Exception as e:
        logger.error(f"Error in /start handler: {e}")
        await update.message.reply_text("❌ Error processing /start command")

async def chat(update: Update, context):
    user_text = update.message.text
    user_id = update.effective_user.id
    logger.info(f"Received message from user {user_id}: {user_text[:50]}...")
    try:
        resp = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": user_text}],
        )
        content = resp.choices[0].message.content if resp and resp.choices else "❌ Erro na resposta da API"
        await update.message.reply_text(content)
        logger.info(f"Sent response to user {user_id}: {content[:50]}...")
    except Exception as e:
        logger.error(f"Error in chat handler for user {user_id}: {e}")
        await update.message.reply_text("❌ Ocorreu um erro ao processar sua mensagem.")

def setup_handlers(application: Application):
    logger.info("Setting up Telegram handlers")
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    logger.info("Handlers added successfully")

@app.post("/webhook")
async def webhook(request: Request):
    global telegram_app
    if telegram_app is None:
        logger.warning("Telegram application not initialized")
        return {"status": "error", "message": "Bot not ready"}
    
    try:
        update_json = await request.json()
        logger.debug(f"Received webhook update: {update_json}")
        update = Update.de_json(update_json, telegram_app.bot)
        if update:
            await telegram_app.process_update(update)
            logger.info("Processed webhook update successfully")
            return {"status": "ok"}
        else:
            logger.warning("Invalid update received")
            return {"status": "error", "message": "Invalid update"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}

@app.get("/")
async def index():
    logger.info("Received GET request to root")
    return {"status": "ok"}

@app.on_event("startup")
async def startup_event():
    global telegram_app
    try:
        logger.info("Initializing Telegram application on startup")
        if not BOT_TOKEN:
            logger.critical("BOT_TOKEN not set in environment variables")
            raise ValueError("BOT_TOKEN is required")
        if not WEBHOOK_URL:
            logger.critical("WEBHOOK_URL not set in environment variables")
            raise ValueError("WEBHOOK_URL is required")

        telegram_app = Application.builder().token(BOT_TOKEN).build()
        setup_handlers(telegram_app)

        logger.info(f"Setting webhook to: {WEBHOOK_URL}")
        await telegram_app.bot.set_webhook(WEBHOOK_URL)
        logger.info("Webhook set successfully")

        logger.info("Initializing Telegram application")
        await telegram_app.initialize()
        # Note: For webhooks, we don't call start() as it starts the updater, which isn't needed
        logger.info("Telegram application initialized")
    except Exception as e:
        logger.critical(f"Failed to initialize bot on startup: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    global telegram_app
    if telegram_app:
        logger.info("Shutting down Telegram application")
        await telegram_app.stop()
        await telegram_app.shutdown()
        logger.info("Telegram application shut down")

if __name__ == "__main__":
    try:
        logger.info(f"Starting Uvicorn on port {PORT}")
        uvicorn.run(app, host="0.0.0.0", port=PORT)
    except Exception as e:
        logger.critical(f"Main thread error: {e}")
        raise    try:
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
