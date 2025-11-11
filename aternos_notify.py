import os
import discord
from mcstatus import JavaServer
from flask import Flask
from threading import Thread
import asyncio

# -----------------------------
# Discord Bot Setup
# -----------------------------
TOKEN = os.environ['DISCORD_TOKEN']  # Discord bot token
CHANNEL_ID = int(os.environ.get('DISCORD_CHANNEL', 1234567890))  # Discord channel to post messages

intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)

# Minecraft server domain (no port needed for Aternos)
MC_SERVER = os.environ.get("MC_SERVER", "example.aternos.me")
server = JavaServer.lookup(MC_SERVER)

async def check_server_status():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    last_online = None

    while not client.is_closed():
        try:
            status = server.status()
            msg = f"Server is online with {status.players.online}/{status.players.max} players!"
            if last_online != status.players.online:
                await channel.send(msg)
                last_online = status.players.online
        except Exception:
            await channel.send("Server is offline!")
            last_online = None

        await asyncio.sleep(60)  # Check every 60 seconds

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    client.loop.create_task(check_server_status())

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
