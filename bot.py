import os
import logging
import io
from PIL import Image, ImageFilter
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
import uvicorn

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token from environment variable
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# Filter functions
async def apply_blur(image_path: str, output_path: str):
    img = Image.open(image_path)
    blurred = img.filter(ImageFilter.BLUR)
    blurred.save(output_path)

async def apply_contour(image_path: str, output_path: str):
    img = Image.open(image_path).convert('L')
    contoured = img.filter(ImageFilter.CONTOUR)
    contoured.save(output_path)

async def apply_rotate(image_path: str, output_path: str):
    img = Image.open(image_path)
    rotated = img.rotate(90, expand=True)
    rotated.save(output_path)

async def apply_segment(image_path: str, output_path: str):
    img = Image.open(image_path).convert('L')
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
    await update.message.reply_text(
        "🎨 Welcome to Image Processing Bot!\n\n"
        "Send me a photo, then choose a filter:\n"
        "• /blur - Apply blur effect\n"
        "• /contour - Detect edges/outline\n"
        "• /rotate - Rotate 90° clockwise\n"
        "• /segment - Convert to B&W\n\n"
        "Just send a photo and then type the command!"
    )

# Handle incoming photos
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_file = await update.message.photo[-1].get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    context.user_data['last_photo'] = photo_bytes
    await update.message.reply_text("📸 Photo received! Now type: /blur, /contour, /rotate, or /segment")

# Generic filter handler
async def handle_filter(update: Update, context: ContextTypes.DEFAULT_TYPE, filter_name: str, filter_func):
    if 'last_photo' not in context.user_data:
        await update.message.reply_text("❌ Please send me a photo first!")
        return
    
    try:
        user_id = update.effective_user.id
        img = Image.open(io.BytesIO(context.user_data['last_photo']))
        
        input_path = f"/tmp/input_{user_id}.jpg"
        output_path = f"/tmp/output_{user_id}_{filter_name}.jpg"
        img.save(input_path)
        
        await filter_func(input_path, output_path)
        
        with open(output_path, 'rb') as f:
            await update.message.reply_photo(photo=f, caption=f"✨ Applied {filter_name} filter!")
        
        os.remove(input_path)
        os.remove(output_path)
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Something went wrong.")

async def blur(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_filter(update, context, "blur", apply_blur)

async def contour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_filter(update, context, "contour", apply_contour)

async def rotate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_filter(update, context, "rotate", apply_rotate)

async def segment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await handle_filter(update, context, "segment", apply_segment)

# Create bot application
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("blur", blur))
application.add_handler(CommandHandler("contour", contour))
application.add_handler(CommandHandler("rotate", rotate))
application.add_handler(CommandHandler("segment", segment))
application.add_handler(MessageHandler(filters.PHOTO, handle_photo))

# Webhook handler
async def telegram_webhook(request):
    body = await request.json()
    update = Update.de_json(body, application.bot)
    await application.process_update(update)
    return JSONResponse({"status": "ok"})

async def health(request):
    return JSONResponse({"status": "healthy"})

# Create Starlette app
starlette_app = Starlette(debug=False, routes=[
    Route("/webhook", telegram_webhook, methods=["POST"]),
    Route("/health", health, methods=["GET"]),
])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(starlette_app, host="0.0.0.0", port=port)
