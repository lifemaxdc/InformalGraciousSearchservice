import discord                 # discord.py
import os                      # for the token
import requests                # for the quote API
import json                    # to read the JSON from the API
import random                   # for randomizing the quotes (encouragement)
from replit import db          # for the replit database which can store data
from keep_alive import keep_alive    #imports web server to keep bot alive
import asyncio
from discord.ext import tasks   #rate limit handling for sad words

# ============== BASIC SETUP / TEST COMMANDS ====================

# Set up proper intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent
client = discord.Client(intents=intents)


#Global Varialbes for quote caches
quote_cache = None
last_quote_time = 0
QUOTE_CACHE_TIME = 60  # Cache quotes for 60 seconds


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
def update_encouragements(encouraging_message):     # adds an encouragement to the list
  if "encouragements" in db.keys():
    encouragements = db["encouragements"]
    encouragements.append(encouraging_message)
    db["encouragements"] = encouragements
  else:
    db["encouragements"] = [encouraging_message]

def delete_encouragment(index):         # deletes an encouragement from the list
  encouragements = db["encouragements"]  # gets the list of encouragements
  if len(encouragements) > index:   # checks if the index is valid
    del encouragements[index]        # deletes the encouragement at the index


# ================ ENCOURAGEMENT RESPONSE TO USER MESSAGES ========================

sad_words= ["sad", "depressed", "unhappy", "angry", "miserable", "depressing"]
last_response_time = 0
COOLDOWN = 5  # 5 seconds cooldown between messages


starter_encouragements = [
  "Cheer up!",
  "Hang in there.",
  "You are a great person!"
]

if "responding" not in db.keys():   #only responds if responding...
  db["responding"] = True            #...is true in the database



# ======================= MESSAGES ==========================

@client.event
async def on_message(message):
  if message.author == client.user:
      return

  if message.content.startswith('^hello'):   #hello command
      await message.channel.send('Hello!')

  elif message.content.startswith('^test'):  #test command
      await message.channel.send('Hush lil bro')

  elif message.content.startswith('^quote'):  #quote command
      quote = get_quote()
      await message.channel.send(quote)

  if db["responding"]:
    global last_response_time
    current_time = asyncio.get_event_loop().time()

    # Only respond if cooldown has passed
    if current_time - last_response_time >= COOLDOWN:
        options = starter_encouragements
        if "encouragements" in db.keys():
            options += list(db["encouragements"])

        if any(word in message.content for word in sad_words):
            await message.channel.send(random.choice(options))
            last_response_time = current_time  # Update last response time


  if message.content.startswith("^new"):  #new encouragement command
    encouraging_message = message.content.split("^new ",1)[1]   #splits the message into two parts
    update_encouragements(encouraging_message)  #adds the encouragement to the list/database
    await message.channel.send("New encouraging message added.")

  if message.content.startswith("^del"):  #allows user to delete an encouragement
    encouragements = []
    if "encouragements" in db.keys():            #verifies its actually in the database
      index = int(message.content.split("^del",1)[1])  #gets the index of the encouragement to delete
      delete_encouragment(index)  #deletes the encouragement at the index
      encouragements = db["encouragements"]  #gets updated list after deletion
    await message.channel.send(encouragements)


  if message.content.startswith("^list"):  #lists all encouragements
    encouragements = []                     #makes an empty list in case there isn't any yet
    if "encouragements" in db.keys():      #verifies its actually in the database
      encouragements = db["encouragements"]  #gets the list of encouragements
    await message.channel.send(encouragements) #sends to discord upon recieving command

  if message.content.startswith("^responding"):  #turns responding (ecouragements) on and off 
    value = message.content.split("^responding ",1)[1]

    if value.lower() == "true":   #turns responding on
      db["responding"] = True      #sets responding to true in the database
      await message.channel.send("Responding is on.")
    else:
      db["responding"] = False       #sets responding to false in the database for anything else
      await message.channel.send("Responding is off.")

# ================== RUN THE BOT ============================
keep_alive()                   #calls web server to keep bot alive
client.run(os.getenv('DCTOKEN'))    # gets DC token from secrets



