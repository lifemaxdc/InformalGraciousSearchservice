from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Hello. I am alive!"

def run():
  app.run(host='0.0.0.0',port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()



#This file is used to keep the bot alive on replit, by running a flask server in the background. It is imported into the main.py file and called with keep_alive()