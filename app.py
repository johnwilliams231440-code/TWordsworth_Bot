import os
import re
import logging
from flask import Flask, request, jsonify
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode
import asyncio
import threading

# ========== CONFIGURATION ==========
TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN environment variable not set")

# Flask app for health checks (required by Render)
app = Flask(__name__)

# Global variable for the bot application
telegram_app = None

# ========== HELPER FUNCTIONS ==========
def count_words(text):
    """Count words in text."""
    words = re.findall(r'\b\w+\b', text)
    return len(words)

def count_characters(text):
    """Count characters (with spaces)."""
    return len(text)

def count_characters_no_spaces(text):
    """Count characters without spaces."""
    return len(re.sub(r'\s', '', text))

def count_lines(text):
    """Count lines in text."""
    return len(text.strip().split('\n')) if text.strip() else 0

def count_sentences(text):
    """Count sentences based on punctuation."""
    sentences = re.split(r'[.!?]+', text)
    return len([s for s in sentences if s.strip()])

def check_poetic_form(text):
    """Check if text matches common poetic forms."""
    words = re.findall(r'\b\w+\b', text.lower())
    lines = text.strip().split('\n')
    word_count = len(words)
    line_count = len(lines)
    
    # Haiku: 3 lines, specific syllable pattern (approximated)
    if line_count == 3 and word_count < 20:
        return "🍃 This looks like it could be a **haiku**! (3 lines, nature themes often work well)"
    
    # Sonnet: 14 lines (simplified detection)
    if line_count == 14 and word_count > 100:
        return "📜 A **sonnet** perhaps? 14 lines of carefully measured verse — Shakespeare would approve!"
    
    # Couplet: 2 lines that rhyme (length check only)
    if line_count == 2 and word_count < 30:
        return "✨ A **couplet**! Two lines walking hand in hand, often seen closing a sonnet."
    
    # Free verse detection
    if line_count > 3 and not (line_count == 14):
        return "🌊 This flows like **free verse** — no fixed rules, just the music of your thoughts."
    
    return "📖 Your words have a rhythm all their own. Keep writing!"

def format_count_response(text):
    """Generate the poetic count response."""
    if not text or not text.strip():
        return "🌿 *Dear friend, send me some words to count.*\n\nSend a message with /count followed by your text, or just reply to this message with your poem."
    
    word_count = count_words(text)
    char_count = count_characters(text)
    char_no_space = count_characters_no_spaces(text)
    line_count = count_lines(text)
    sentence_count = count_sentences(text)
    
    # Poetic opening based on word count
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
    
    # --- FIXED HERE: Closed the f-string and completed the output ---
    response = f"""📖 *Count Wordsworth's Report*

_{opening}_

✨ *The Tapestry of Your Text:*
• Words: **{word_count}**
• Characters (with spaces): **{char_count}**
• Characters (no spaces): **{char_no_space}**
• Lines: **{line_count}**
• Sentences: **{sentence_count}**

{check_poetic_form(text)}"""
    return response

# ========== TELEGRAM BOT HANDLERS ==========
async def start(update: Update, context):
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "Greetings! I am Count Wordsworth. Send me any text or poem, and I will analyze its structure for you.",
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_count(update: Update, context):
    """Handle the /count command or direct text messages."""
    # If it's a command, take the text after /count. Otherwise, take the whole message text.
    text = " ".join(context.args) if context.args else update.message.text
    
    # Remove the command string if they typed it directly
    if text.startswith('/count'):
        text = text.replace('/count', '', 1).strip()

    response = format_count_response(text)
    await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)

# ========== FLASK & BOT RUNNERS ==========
@app.route('/')
def health_check():
    """Health check endpoint for Render."""
    return jsonify({"status": "healthy"}), 200

def run_flask():
    """Run Flask on port 10000 (Render default)."""
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def main():
    """Start the bot using polling."""
    global telegram_app
    
    # Build the application
    telegram_app = Application.builder().token(TOKEN).build()

    # Add handlers
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("count", handle_count))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_count))

    # Run Flask in a background thread so Render health check doesn't timeout
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Start the Telegram Bot polling loop
    print("Starting bot...")
    telegram_app.run_polling()

if __name__ == '__main__':
    main()
