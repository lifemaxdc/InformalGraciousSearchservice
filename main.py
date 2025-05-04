import discord                 # import discord.py    
import os                      # for the token



client = discord.Client()       # client is our connection to discord


@client.event                    # we define an event here
async def on_ready():         # this event is called when the bot is ready (setup)
    print('LifeMax: We have logged in as {0.user}'.format(client))         
        # print to console only

@client.event
async def on_message(message):      # these functions are from discord.py library 
    if message.author == client.user:
        return

    if message.content.startswith('^hello'):
      await message.channel.send('Hello!')

client.run(os.getenv('DCTOKEN')) #gets discord token from hidden .env file