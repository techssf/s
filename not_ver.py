import os
import logging
import asyncio
from fastapi import FastAPI, Request
import uvicorn
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from groq import Groq
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_KEY = os.getenv("GROQ_API_KEY")
PORT = int(os.getenv("PORT", 10000))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://s-2jdr.onrender.com") 

# Initialize Groq client
if not GROQ_KEY:
    logger.critical("GROQ_API_KEY not set in environment variables")
    raise ValueError("GROQ_API_KEY is required")
groq_client = Groq(api_key=GROQ_KEY)

# Initialize FastAPI app
app = FastAPI()

# Global variable for Telegram application
telegram_app = None

async def test_groq_connection():
    """Test Groq API connection and find working model"""
    models_to_test = [
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "llama3-8b-8192",
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
    
    models_to_try = [
        "llama-3.1-8b-instant",
        "llama3-70b-8192",
        "llama3-8b-8192",
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
    return {"status": "Bot is running", "webhook": "active"}

@app.post("/webhook")
async def webhook_handler(request: Request):
    """Handle incoming webhook updates from Telegram"""
    try:
        # Get the raw request body
        body = await request.body()
        
        # Parse the JSON
        update_data = json.loads(body.decode('utf-8'))
        logger.info(f"Received webhook update: {update_data.get('update_id', 'unknown')}")
        
        # Create Update object
        update = Update.de_json(update_data, telegram_app.bot)
        
        # Process the update
        if telegram_app:
            await telegram_app.process_update(update)
            
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}

async def setup_webhook():
    """Setup webhook instead of polling to avoid conflicts"""
    try:
        if not telegram_app:
            return
            
        webhook_url = f"{WEBHOOK_URL}/webhook"
        logger.info(f"Setting up webhook: {webhook_url}")
        
        # Delete any existing webhook
        await telegram_app.bot.delete_webhook(drop_pending_updates=True)
        logger.info("Cleared existing webhook")
        
        # Set the new webhook
        await telegram_app.bot.set_webhook(
            url=webhook_url,
            allowed_updates=["message", "callback_query"]
        )
        logger.info(f"✅ Webhook set successfully: {webhook_url}")
        
    except Exception as e:
        logger.error(f"Error setting up webhook: {e}")
        raise

async def init_telegram_app():
    """Initialize Telegram application"""
    global telegram_app
    try:
        logger.info("Initializing Telegram application")
        if not BOT_TOKEN:
            logger.critical("BOT_TOKEN not set in environment variables")
            raise ValueError("BOT_TOKEN is required")

        telegram_app = Application.builder().token(BOT_TOKEN).build()
        setup_handlers(telegram_app)

        # Initialize the application
        await telegram_app.initialize()
        await telegram_app.start()
        
        # Setup webhook
        await setup_webhook()
        
        logger.info("✅ Telegram application initialized with webhook")
        
    except Exception as e:
        logger.critical(f"Failed to initialize Telegram app: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """FastAPI startup event"""
    logger.info("FastAPI starting up...")
    
    # Test Groq connection
    working_model = await test_groq_connection()
    if not working_model:
        logger.warning("No working Groq models found, but continuing...")
    
    # Initialize Telegram
    await init_telegram_app()
    
    logger.info("✅ Application startup complete")

@app.on_event("shutdown") 
async def shutdown_event():
    """FastAPI shutdown event"""
    logger.info("FastAPI shutting down...")
    
    if telegram_app:
        try:
            await telegram_app.bot.delete_webhook()
            await telegram_app.stop()
            await telegram_app.shutdown()
            logger.info("✅ Telegram application shut down")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

def main():
    """Main function to run the application"""
    logger.info("Starting application with webhook mode")
    
    # Run the FastAPI app
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=PORT,
        log_level="info"
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.critical(f"Application error: {e}")
        raise
