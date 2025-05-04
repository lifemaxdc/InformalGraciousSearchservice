import discord                 # import discord.py    
import os                      # for the token


intents = discord.Intents.default() #Creates intents object
client = discord.Client(intents=intents)  # pass intents to client


@client.event                    # we define an event here
async def on_ready():         # this event is called when the bot is ready (setup)
    print('Hey King, we have logged in as {0.user}'.format(client))         
        # print to console only

@client.event
async def on_message(message):      # these functions are from discord.py library 
    if message.author == client.user:
        return

    if message.content.startswith('^hello'):
      print('Hello!')

client.run(os.getenv('DCTOKEN')) #gets discord token from hidden .env file