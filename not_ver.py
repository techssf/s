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

# Create a simple lock file to prevent multiple instances
import tempfile
import fcntl

LOCK_FILE = "/tmp/bot_instance.lock"

def acquire_lock():
    """Acquire a file lock to ensure only one bot instance runs"""
    try:
        lock_file = open(LOCK_FILE, 'w')
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        logger.info("Successfully acquired instance lock")
        return lock_file
    except (IOError, OSError) as e:
        logger.error(f"Could not acquire lock - another instance may be running: {e}")
        return None

# Initialize Groq client
if not GROQ_KEY:
    logger.critical("GROQ_API_KEY not set in environment variables")
    raise ValueError("GROQ_API_KEY is required")
groq_client = Groq(api_key=GROQ_KEY)

async def clear_bot_conflicts():
    """Clear any existing bot conflicts"""
    try:
        # Create a temporary bot instance just for cleanup
        from telegram import Bot
        temp_bot = Bot(token=BOT_TOKEN)
        
        # Delete webhook
        await temp_bot.delete_webhook(drop_pending_updates=True)
        logger.info("Cleared existing webhooks and pending updates")
        
        # Close the temporary bot
        await temp_bot.close()
        
        # Wait a bit to ensure cleanup
        await asyncio.sleep(2)
        
    except Exception as e:
        logger.warning(f"Error during conflict cleanup: {e}")
        pass
    """Test Groq API connection and find working model"""
    models_to_test = [
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "llama3-70b-8192", 
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
        "gemma-7b-it"
    ]
    
    logger.info("Testing Groq API connection...")
    
    for model in models_to_test:
        try:
            resp = groq_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            if resp and resp.choices:
                logger.info(f"✅ Model {model} is working!")
                return model
        except Exception as e:
            logger.warning(f"❌ Model {model} failed: {e}")
            continue
    
    logger.error("❌ No working Groq models found!")
    return None

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
    
    # List of models to try (in order of preference)
    models_to_try = [
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant", 
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768",
        "gemma-7b-it"
    ]
    
    for model in models_to_try:
        try:
            logger.info(f"Trying model: {model}")
            resp = groq_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Você é um assistente útil. Responda de forma clara e concisa."},
                    {"role": "user", "content": user_text}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            if resp and resp.choices and resp.choices[0].message.content:
                content = resp.choices[0].message.content
                await update.message.reply_text(content)
                logger.info(f"Success with model {model}. Response sent to user {user_id}")
                return
            else:
                logger.warning(f"Empty response from model {model}")
                continue
                
        except Exception as e:
            logger.error(f"Error with model {model} for user {user_id}: {e}")
            continue
    
    # If all models failed
    error_msg = "❌ Desculpe, todos os modelos estão indisponíveis no momento. Tente novamente mais tarde."
    await update.message.reply_text(error_msg)
    logger.error(f"All models failed for user {user_id}")

def setup_handlers(application: Application):
    logger.info("Setting up Telegram handlers")
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    logger.info("Handlers added successfully")

@app.get("/")
async def index():
    logger.info("Received GET request to root")
    return {"status": "ok"}

@app.post("/")
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
        
        # Clear any existing webhooks before starting polling
        await telegram_app.bot.delete_webhook()
        logger.info("Cleared existing webhooks")
        
        await telegram_app.updater.start_polling(
            drop_pending_updates=True,  # Drop any pending updates
            allowed_updates=None
        )
        logger.info("Telegram bot polling started")
        
        # Keep running indefinitely
        while True:
            await asyncio.sleep(10)  # Increased sleep time
        
    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")
        raise

async def run_server():
    try:
        logger.info(f"Starting Uvicorn on port {PORT}")
        config = uvicorn.Config(app, host="0.0.0.0", port=PORT, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

async def main():
    try:
        logger.info("Starting main application")
        
        # Clear any existing bot conflicts first
        await clear_bot_conflicts()
        
        # Test Groq connection first
        working_model = await test_groq_connection()
        if not working_model:
            logger.critical("No working Groq models found. Check your API key and model availability.")
            # Don't return, let it try to run anyway
        
        # Create both tasks
        bot_task = asyncio.create_task(run_bot())
        server_task = asyncio.create_task(run_server())
        
        logger.info("Bot and server tasks created")
        
        # Wait for both tasks to complete (they shouldn't under normal circumstances)
        done, pending = await asyncio.wait([bot_task, server_task], return_when=asyncio.FIRST_EXCEPTION)
        
        # If one task fails, cancel the others
        for task in pending:
            task.cancel()
            
        # Re-raise any exceptions
        for task in done:
            if task.exception():
                raise task.exception()
        
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
    lock_file = None
    try:
        logger.info("Starting main application")
        
        # Try to acquire lock first
        lock_file = acquire_lock()
        if lock_file is None:
            logger.critical("Another bot instance is already running!")
            exit(1)
            
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.critical(f"Main thread error: {e}")
        raise
    finally:
        # Release lock
        if lock_file:
            try:
                lock_file.close()
                import os
                os.remove(LOCK_FILE)
            except:
                pass
