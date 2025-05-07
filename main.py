import discord
import os
import json
import random
import sqlite3
import requests
import asyncio
from discord.ext import tasks
from keep_alive import keep_alive

# ============== DATABASE SETUP ====================

conn = sqlite3.connect('bot_data.db')  # only use ONE connection
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

# ============== DISCORD BOT SETUP ====================

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# ============== GLOBALS ====================

quote_cache = None
last_quote_time = 0
QUOTE_CACHE_TIME = 60

last_response_time = 0
COOLDOWN = 5

starter_encouragements = [
    "Cheer up!",
    "Hang in there.",
    "You are a great person!"
]

sad_words = ["sad", "depressed", "unhappy", "angry", "miserable", "depressing"]

# ============== BOT EVENTS ====================

@client.event
async def on_ready():
    print(f"Hey King, we have logged in as {client.user}", flush=True)

@client.event
async def on_message(message):
    try:
        if message.author == client.user:
            return

        if message.content.startswith('^hello'):
            await message.channel.send('Hello!')

        elif message.content.startswith('^test'):
            await message.channel.send('Hush lil bro')

        elif message.content.startswith('^quote'):
            quote = get_quote()
            await message.channel.send(quote)

        if get_responding():
            global last_response_time
            current_time = asyncio.get_event_loop().time()

            if current_time - last_response_time >= COOLDOWN:
                options = starter_encouragements + get_encouragements()

                if any(word in message.content for word in sad_words):
                    await message.channel.send(random.choice(options))
                    last_response_time = current_time

        if message.content.startswith("^new"):
            encouraging_message = message.content.split("^new ", 1)[1]
            update_encouragements(encouraging_message)
            await message.channel.send("New encouraging message added.")

        if message.content.startswith("^del"):
            try:
                index = int(message.content.split("^del", 1)[1].strip())
                delete_encouragement(index)
                encouragements = get_encouragements()
                await message.channel.send(encouragements)
            except (ValueError, IndexError):
                await message.channel.send("Please specify a valid index to delete.")

        if message.content.startswith("^list"):
            encouragements = get_encouragements()
            await message.channel.send(encouragements)

        if message.content.startswith("^responding"):
            try:
                value = message.content.split("^responding ", 1)[1]
                set_responding(value.lower() == "true")
                await message.channel.send(f"Responding is {'on' if get_responding() else 'off'}.")
            except IndexError:
                await message.channel.send("Please specify 'true' or 'false'.")

    except discord.errors.HTTPException as e:
        if e.status == 429:
            print(f"Rate limited! Waiting {e.retry_after} seconds...", flush=True)
            await asyncio.sleep(e.retry_after + 1)
        else:
            raise e

# ============== FUNCTIONS ====================

def get_quote():
    global quote_cache, last_quote_time
    current_time = asyncio.get_event_loop().time()

    if quote_cache is None or (current_time - last_quote_time) > QUOTE_CACHE_TIME:
        response = requests.get("https://zenquotes.io/api/random")
        json_data = json.loads(response.text)
        quote_cache = json_data[0]['q'] + " -" + json_data[0]['a']
        last_quote_time = current_time

    return quote_cache

def update_encouragements(encouraging_message):
    cursor.execute("INSERT INTO encouragements (message) VALUES (?)", (encouraging_message,))
    conn.commit()

def delete_encouragement(index):
    cursor.execute("SELECT id, message FROM encouragements ORDER BY id")
    encouragements = cursor.fetchall()

    if index < len(encouragements):
        encouragement_id = encouragements[index][0]
        cursor.execute("DELETE FROM encouragements WHERE id = ?", (encouragement_id,))
        conn.commit()

def get_encouragements():
    cursor.execute("SELECT message FROM encouragements ORDER BY id")
    return [row[0] for row in cursor.fetchall()]

def get_responding():
    cursor.execute("SELECT value FROM settings WHERE key = 'responding'")
    result = cursor.fetchone()
    return True if result is None else result[0].lower() == 'true'

def set_responding(value):
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                   ('responding', str(value)))
    conn.commit()

# ============== RUN BOT ====================

keep_alive()
print(f"Loaded token? {'Yes' if os.getenv('DCTOKEN') else 'No'}", flush=True)
client.run(os.getenv("DCTOKEN"))
