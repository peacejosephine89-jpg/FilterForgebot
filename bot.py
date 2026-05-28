import os
import sys
import asyncio
import logging

# FORCE all output to be visible immediately
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

print("=" * 60, flush=True)
print("BOT STARTING - Phase 1: Initialization", flush=True)
print(f"Python version: {sys.version}", flush=True)
print(f"Current directory: {os.getcwd()}", flush=True)
print("=" * 60, flush=True)

# Configure logging to also print to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

print("Phase 2: Importing libraries...", flush=True)

try:
    from telegram import Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    print("✓ python-telegram-bot imported", flush=True)
except Exception as e:
    print(f"❌ Failed to import telegram: {e}", flush=True)
    sys.exit(1)

try:
    from PIL import Image, ImageFilter
    print("✓ Pillow imported", flush=True)
except Exception as e:
    print(f"❌ Failed to import Pillow: {e}", flush=True)
    sys.exit(1)

print("Phase 3: Getting bot token...", flush=True)
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

if not TOKEN:
    print("❌ ERROR: TELEGRAM_BOT_TOKEN environment variable not set!", flush=True)
    print("Please add it in Render dashboard: Environment → Environment Variables", flush=True)
    sys.exit(1)

print(f"✓ Bot token loaded (length: {len(TOKEN)})", flush=True)

# Simple command handlers for testing
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    print(f"📨 Received /start from {user.first_name} (ID: {user.id})", flush=True)
    await update.message.reply_text(
        "🎉 Bot is alive and working!\n\n"
        "Send me a photo, then use:\n"
        "/blur - Apply blur\n"
        "/contour - Detect edges\n"
        "/rotate - Rotate 90°\n"
        "/segment - B&W conversion"
    )

async def blur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Processing blur... (demo mode)")

async def contour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📐 Processing contour... (demo mode)")

async def rotate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Processing rotate... (demo mode)")

async def segment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚫ Processing segment... (demo mode)")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"📸 Received photo from user {update.effective_user.id}", flush=True)
    await update.message.reply_text("📷 Photo received! Use /blur, /contour, /rotate, or /segment")

print("Phase 4: Building application...", flush=True)

def main():
    try:
        # Create application
        application = Application.builder().token(TOKEN).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("blur", blur))
        application.add_handler(CommandHandler("contour", contour))
        application.add_handler(CommandHandler("rotate", rotate))
        application.add_handler(CommandHandler("segment", segment))
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        
        print("✓ Application built successfully", flush=True)
        print("=" * 60, flush=True)
        print("✅ BOT IS RUNNING! Waiting for messages...", flush=True)
        print("=" * 60, flush=True)
        
        # Start polling (this blocks until stopped)
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        print(f"❌ Fatal error in main: {e}", flush=True)
        import traceback
        traceback.print_exc(file=sys.stdout)
        sys.exit(1)

if __name__ == "__main__":
    main()
