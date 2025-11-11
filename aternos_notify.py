import os
import discord
from flask import Flask
from threading import Thread

# -----------------------------
# Discord Bot Setup
# -----------------------------
TOKEN = os.environ['DISCORD_TOKEN']  # Make sure this env variable is set in Render
intents = discord.Intents.default()
intents.messages = True  # Adjust according to what your bot needs
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

# Example: simple message response
@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.lower() == "!ping":
        await message.channel.send("Pong!")

# -----------------------------
# Flask Web Server (for Render)
# -----------------------------
app = Flask(__name__)

@app.route("/healthz")
def health_check():
    return "OK", 200

def run_flask():
    # Render expects port 10000 by default for Python web services
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# -----------------------------
# Start Flask server in a separate thread
# -----------------------------
Thread(target=run_flask).start()

# -----------------------------
# Start Discord Bot
# -----------------------------
client.run(TOKEN)
