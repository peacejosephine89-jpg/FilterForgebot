import os
import logging
import io
from PIL import Image, ImageFilter
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import random

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token from environment variable
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# Dictionary to track user states (which filter they want to apply)
user_states = {}

# Filter functions
async def apply_blur(image_path: str, output_path: str):
    img = Image.open(image_path)
    blurred = img.filter(ImageFilter.BLUR)
    blurred.save(output_path)

async def apply_contour(image_path: str, output_path: str):
    img = Image.open(image_path).convert('L')  # Convert to grayscale for better contour
    contoured = img.filter(ImageFilter.CONTOUR)
    contoured.save(output_path)

async def apply_rotate(image_path: str, output_path: str):
    img = Image.open(image_path)
    rotated = img.rotate(90, expand=True)  # 90 degrees clockwise
    rotated.save(output_path)

async def apply_segment(image_path: str, output_path: str):
    # Segment: pixels > 100 become white (255), others black (0)
    img = Image.open(image_path).convert('L')  # Grayscale
    pixels = img.load()
    for i in range(img.size[0]):
        for j in range(img.size[1]):
            if pixels[i, j] > 100:
                pixels[i, j] = 255
            else:
                pixels[i, j] = 0
    img.save(output_path)

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["/blur", "/contour"],
        ["/rotate", "/segment"]
    ]
    await update.message.reply_text(
        "🎨 Welcome to Image Processing Bot!\n\n"
        "Send me a photo, then choose a filter:\n"
        "• /blur - Apply blur effect\n"
        "• /contour - Detect edges/outline\n"
        "• /rotate - Rotate 90° clockwise\n"
        "• /segment - Convert to B&W (threshold 100)\n\n"
        "Just send a photo and then type the command!",
        reply_markup={"keyboard": keyboard, "resize_keyboard": True}
    )

# Handle incoming photos
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    photo_file = await update.message.photo[-1].get_file()
    
    # Download photo to bytes
    photo_bytes = await photo_file.download_as_bytearray()
    
    # Save temporarily (in memory for now, or we can store user_id -> photo mapping)
    context.user_data['last_photo'] = photo_bytes
    context.user_data['last_photo_format'] = 'jpg'  # Telegram sends JPEG
    
    await update.message.reply_text("📸 Photo received! Now type one of the commands: /blur, /contour, /rotate, /segment")

# Generic filter handler
async def handle_filter(update: Update, context: ContextTypes.DEFAULT_TYPE, filter_name: str, filter_func):
    user_id = update.effective_user.id
    
    # Check if user has sent a photo
    if 'last_photo' not in context.user_data:
        await update.message.reply_text("❌ Please send me a photo first!")
        return
    
    # Process the image
    try:
        # Load image from bytes
        photo_bytes = context.user_data['last_photo']
        img = Image.open(io.BytesIO(photo_bytes))
        
        # Save temporarily to process
        input_path = f"/tmp/input_{user_id}.jpg"
        output_path = f"/tmp/output_{user_id}_{filter_name}.jpg"
        img.save(input_path)
        
        # Apply the filter
        await filter_func(input_path, output_path)
        
        # Send result back
        with open(output_path, 'rb') as f:
            await update.message.reply_photo(
                photo=f,
                caption=f"✨ Applied {filter_name} filter!"
            )
        
        # Cleanup
        os.remove(input_path)
        os.remove(output_path)
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await update.message.reply_text("❌ Sorry, something went wrong while processing your image.")

# Individual command handlers
async def blur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_filter(update, context, "blur", apply_blur)

async def contour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_filter(update, context, "contour", apply_contour)

async def rotate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_filter(update, context, "rotate", apply_rotate)

async def segment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_filter(update, context, "segment", apply_segment)

# Webhook handler for Render
async def webhook(request):
    """Handle incoming webhook requests from Telegram"""
    from telegram import Update as TelegramUpdate
    import json
    
    try:
        body = await request.json()
        update = TelegramUpdate.de_json(body, app.bot)
        await app.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"status": "error"}, 500

# Health check endpoint for Render
async def health(request):
    return {"status": "healthy"}

# Main entry point
if __name__ == "__main__":
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.responses import JSONResponse
    
    # Create the Telegram application
    app = ApplicationBuilder().token(TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("blur", blur))
    app.add_handler(CommandHandler("contour", contour))
    app.add_handler(CommandHandler("rotate", rotate))
    app.add_handler(CommandHandler("segment", segment))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    
    # Create Starlette app for webhook
    async def telegram_webhook(request):
        body = await request.json()
        update = Update.de_json(body, app.bot)
        await app.process_update(update)
        return JSONResponse({"status": "ok"})
    
    starlette_app = Starlette(debug=False, routes=[
        Route("/webhook", telegram_webhook, methods=["POST"]),
        Route("/health", lambda r: JSONResponse({"status": "healthy"}), methods=["GET"]),
    ])
    
    # Run with uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)
