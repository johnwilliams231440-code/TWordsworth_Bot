import os
import re
import asyncio
from flask import Flask, request, jsonify
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode

# ========== CONFIGURATION ==========
TOKEN = os.environ.get("TELEGRAM_TOKEN")
# Example: https://your-app-name.onrender.com
RENDER_EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL") 

if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable not set")

# Initialize Flask
app = Flask(__name__)

# Initialize Telegram Application globally
telegram_app = Application.builder().token(TOKEN).build()

# ========== HELPER FUNCTIONS ==========
def count_words(text):
    return len(re.findall(r'\b\w+\b', text))

def count_characters(text):
    return len(text)

def count_characters_no_spaces(text):
    return len(re.sub(r'\s', '', text))

def count_lines(text):
    return len(text.strip().split('\n')) if text.strip() else 0

def count_sentences(text):
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])

def check_poetic_form(text):
    words = re.findall(r'\b\w+\b', text.lower())
    lines = text.strip().split('\n')
    word_count = len(words)
    line_count = len(lines)
    
    if line_count == 3 and word_count < 20:
        return "🍃 This looks like it could be a **haiku**! (3 lines, nature themes often work well)"
    if line_count == 14 and word_count > 100:
        return "📜 A **sonnet** perhaps? 14 lines of carefully measured verse — Shakespeare would approve!"
    if line_count == 2 and word_count < 30:
        return "✨ A **couplet**! Two lines walking hand in hand, often seen closing a sonnet."
    if line_count > 3 and not (line_count == 14):
        return "🌊 This flows like **free verse** — no fixed rules, just the music of your thoughts."
    return "📖 Your words have a rhythm all their own. Keep writing!"

def format_count_response(text):
    if not text or not text.strip():
        return "🌿 *Dear friend, send me some words to count.*\n\nSend a message with /count followed by your text, or just reply to this message with your poem."
    
    word_count = count_words(text)
    char_count = count_characters(text)
    char_no_space = count_characters_no_spaces(text)
    line_count = count_lines(text)
    sentence_count = count_sentences(text)
    
    if word_count == 0:
        opening = "The page whispers silence..."
    elif word_count < 10:
        opening = "A gentle breath of words..."
    elif word_count < 30:
        opening = "A modest gathering of syllables..."
    elif word_count < 100:
        opening = "A flowing stream of language..."
    else:
        opening = "A grand procession of prose and poetry..."
    
    return f"""📖 *Count Wordsworth's Report*

_{opening}_

✨ *The Tapestry of Your Text:*
• Words: **{word_count}**
• Characters (with spaces): **{char_count}**
• Characters (no spaces): **{char_no_space}**
• Lines: **{line_count}**
• Sentences: **{sentence_count}**

{check_poetic_form(text)}"""

# ========== TELEGRAM BOT HANDLERS ==========
async def start(update: Update, context):
    await update.message.reply_text(
        "Greetings! I am Count Wordsworth. Send me any text or poem, and I will analyze its structure for you.",
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_count(update: Update, context):
    text = " ".join(context.args) if context.args else update.message.text
    if text and text.startswith('/count'):
        text = text.replace('/count', '', 1).strip()

    response = format_count_response(text)
    await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)

# Register Handlers to the Application engine
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("count", handle_count))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_count))

# ========== FLASK ROUTES (WEBHOOK INTERFACE) ==========
@app.route('/')
def health_check():
    return jsonify({"status": "healthy", "mode": "webhook"}), 200

@app.route(f'/{TOKEN}', methods=['POST'])
def telegram_webhook():
    """Receives incoming messages directly from Telegram."""
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    
    # Process the update smoothly using the underlying framework loop
    asyncio.run(telegram_app.process_update(update))
    return "OK", 200

def setup_webhook():
    """Tells Telegram where to send data on startup."""
    if RENDER_EXTERNAL_URL:
        webhook_url = f"{RENDER_EXTERNAL_URL.rstrip('/')}/{TOKEN}"
        print(f"Setting webhook destination to: {webhook_url}")
        
        asyncio.run(telegram_app.initialize())
        asyncio.run(telegram_app.bot.set_webhook(url=webhook_url))
    else:
        print("Warning: RENDER_EXTERNAL_URL environment variable missing. Webhook setup bypassed.")

# ========== MAIN ENTRYPOINT ==========
if __name__ == '__main__':
    # Step 1: Register the live url hook with Telegram
    setup_webhook()
    
    # Step 2: Fire up the native webserver
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
