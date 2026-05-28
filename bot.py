import os
import sys
import logging

# Force print to see if script starts
print("=" * 50)
print("Bot script started!")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")
print(f"Files in directory: {os.listdir('.')}")
print("=" * 50)

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Try to import required libraries
try:
    print("Importing telegram...")
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    print("✓ Telegram imported")
except Exception as e:
    print(f"❌ Failed to import telegram: {e}")
    sys.exit(1)

try:
    print("Importing PIL...")
    from PIL import Image, ImageFilter
    print("✓ PIL imported")
except Exception as e:
    print(f"❌ Failed to import PIL: {e}")
    sys.exit(1)

# Get bot token
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
print(f"Bot token loaded: {'✅ Yes' if TOKEN else '❌ No'}")

if not TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
    print("❌ ERROR: TELEGRAM_BOT_TOKEN not found!")
    sys.exit(1)

# Simple start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Received /start from user {update.effective_user.id}")
    await update.message.reply_text("Hello! I am alive! Send me a photo.")

# Simple photo handler
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Received photo from user {update.effective_user.id}")
    await update.message.reply_text("Thanks for the photo! (processing coming soon)")

# Main function
def main():
    print("\n🤖 Creating bot application...")
    application = Application.builder().token(TOKEN).build()
    
    print("Adding handlers...")
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    print("Starting polling...")
    print("✅ Bot is running! Waiting for messages...\n")
    
    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
