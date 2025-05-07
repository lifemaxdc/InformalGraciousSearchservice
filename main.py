import discord                 # discord.py
import os                      # for the token
import json                    # to read the JSON from the API
import random                  # for randomizing the quotes (encouragement)
import sqlite3                 # replacement for replit database
db = sqlite3.connect('/tmp/bot.db')
from keep_alive import keep_alive    # imports web server to keep bot alive
import asyncio
from discord.ext import tasks   # rate limit handling for sad words

# ============== BASIC SETUP / TEST COMMANDS ====================

# Initialize SQLite database connection
conn = sqlite3.connect('bot_data.db')
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS encouragements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
''')
conn.commit()

# Set up proper intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
client = discord.Client(intents=intents)

# Global Variables for quote caches
quote_cache = None
last_quote_time = 0
QUOTE_CACHE_TIME = 60  # Cache quotes for 60 seconds

# Cooldown variables for rate limiting
last_response_time = 0
COOLDOWN = 5  # 5 seconds cooldown between messages

# Starter encouragements
starter_encouragements = [
    "Cheer up!",
    "Hang in there.",
    "You are a great person!"
]

# Sad words to respond to
sad_words = ["sad", "depressed", "unhappy", "angry", "miserable", "depressing"]

@client.event
async def on_ready():
    print(f'Hey King, we have logged in as {client.user}')   # prints to console

# ====================== API QUOTES =========================

def get_quote():
    global quote_cache, last_quote_time
    current_time = asyncio.get_event_loop().time()

    # If cache is empty or expired, fetch a new quote
    if quote_cache is None or (current_time - last_quote_time) > QUOTE_CACHE_TIME:
        response = requests.get("https://zenquotes.io/api/random")
        json_data = json.loads(response.text)
        quote_cache = json_data[0]['q'] + " -" + json_data[0]['a']
        last_quote_time = current_time

    return quote_cache

# ======================= ENCOURAGEMENT DATABASE ==========================

def update_encouragements(encouraging_message):
    """Adds an encouragement to the database"""
    cursor.execute("INSERT INTO encouragements (message) VALUES (?)", (encouraging_message,))
    conn.commit()

def delete_encouragement(index):
    """Deletes an encouragement from the database"""
    # Get all encouragements
    cursor.execute("SELECT id, message FROM encouragements ORDER BY id")
    encouragements = cursor.fetchall()

    if index < len(encouragements):
        # Delete the encouragement at the specified index
        encouragement_id = encouragements[index][0]
        cursor.execute("DELETE FROM encouragements WHERE id = ?", (encouragement_id,))
        conn.commit()

def get_encouragements():
    """Returns all encouragements from the database"""
    cursor.execute("SELECT message FROM encouragements ORDER BY id")
    return [row[0] for row in cursor.fetchall()]

def get_responding():
    """Returns the current responding status"""
    cursor.execute("SELECT value FROM settings WHERE key = 'responding'")
    result = cursor.fetchone()
    return True if result is None else result[0].lower() == 'true'

def set_responding(value):
    """Sets the responding status"""
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", 
                  ('responding', str(value)))
    conn.commit()

# ======================= MESSAGES ==========================

@client.event
async def on_message(message):
    try:
        if message.author == client.user:
            return

        if message.content.startswith('^hello'):   # hello command
            await message.channel.send('Hello!')

        elif message.content.startswith('^test'):  # test command
            await message.channel.send('Hush lil bro')

        elif message.content.startswith('^quote'):  # quote command
            quote = get_quote()
            await message.channel.send(quote)

        if get_responding():
            global last_response_time
            current_time = asyncio.get_event_loop().time()

            # Only respond if cooldown has passed
            if current_time - last_response_time >= COOLDOWN:
                options = starter_encouragements + get_encouragements()

                if any(word in message.content for word in sad_words):
                    await message.channel.send(random.choice(options))
                    last_response_time = current_time  # Update last response time

        if message.content.startswith("^new"):  # new encouragement command
            encouraging_message = message.content.split("^new ", 1)[1]
            update_encouragements(encouraging_message)
            await message.channel.send("New encouraging message added.")

        if message.content.startswith("^del"):  # delete encouragement command
            try:
                index = int(message.content.split("^del", 1)[1].strip())
                delete_encouragement(index)
                encouragements = get_encouragements()
                await message.channel.send(encouragements)
            except (ValueError, IndexError):
                await message.channel.send("Please specify a valid index to delete.")

        if message.content.startswith("^list"):  # list all encouragements
            encouragements = get_encouragements()
            await message.channel.send(encouragements)

        if message.content.startswith("^responding"):  # toggle responding
            try:
                value = message.content.split("^responding ", 1)[1]
                set_responding(value.lower() == "true")
                await message.channel.send(f"Responding is {'on' if get_responding() else 'off'}.")
            except IndexError:
                await message.channel.send("Please specify 'true' or 'false'.")

    except discord.errors.HTTPException as e:
        if e.status == 429:  # Rate limited
            print(f"Rate limited! Waiting {e.retry_after} seconds...")
            await asyncio.sleep(e.retry_after + 1)
        else:
            raise e

# ================== RUN THE BOT ============================
keep_alive()                   # calls web server to keep bot alive
client.run(os.getenv('DCTOKEN'))    # gets DC token from secrets