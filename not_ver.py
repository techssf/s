import os
import logging
import asyncio
from fastapi import FastAPI
import uvicorn
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from groq import Groq

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Only console output for Render
    ]
)
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
PORT = int(os.getenv("PORT", 10000))

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
        # Use a supported model instead of the decommissioned one
        resp = groq_client.chat.completions.create(
            model="llama3-8b-8192",  # Updated to supported model
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

@app.get("/")
async def index():
    logger.info("Received GET request to root")
    return {"status": "ok"}

@app.post("/")  # Add POST handler for potential webhooks
async def webhook():
    return {"status": "ok"}

async def run_bot():
    global telegram_app
    try:
        logger.info("Initializing Telegram application")
        if not BOT_TOKEN:
            logger.critical("BOT_TOKEN not set in environment variables")
            raise ValueError("BOT_TOKEN is required")

        telegram_app = Application.builder().token(BOT_TOKEN).build()
        setup_handlers(telegram_app)

        logger.info("Starting Telegram bot with polling")
        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.updater.start_polling()
        logger.info("Telegram bot polling started")
        
        # Fixed: Use the updater's idle method instead of wait
        return telegram_app.updater.idle()
        
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")
        raise

async def main():
    try:
        logger.info("Starting main application")
        
        # Start the Telegram bot in the background
        bot_task = asyncio.create_task(run_bot())
        logger.info("Bot task created")

        # Start Uvicorn server
        logger.info(f"Starting Uvicorn on port {PORT}")
        config = uvicorn.Config(app, host="0.0.0.0", port=PORT, log_level="info")
        server = uvicorn.Server(config)
        
        # Run both the bot and server concurrently
        await asyncio.gather(
            server.serve(),
            bot_task
        )
        
    except Exception as e:
        logger.critical(f"Main loop error: {e}")
        raise
    finally:
        # Ensure cleanup if the server stops
        if telegram_app:
            logger.info("Stopping Telegram bot")
            try:
                await telegram_app.updater.stop()
                await telegram_app.stop()
                await telegram_app.shutdown()
                logger.info("Telegram bot shut down")
            except Exception as e:
                logger.error(f"Error during bot shutdown: {e}")

if __name__ == "__main__":
    try:
        logger.info("Starting main application")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.critical(f"Main thread error: {e}")
        raise
