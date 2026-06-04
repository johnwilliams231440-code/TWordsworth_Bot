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
    
    response = f"""📖 *Count Wordsworth's Report*

{opening}
