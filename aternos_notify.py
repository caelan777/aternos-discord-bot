import os
import discord
import asyncio
from mcstatus import MinecraftServer
from flask import Flask
from threading import Thread

# -----------------------------
# Discord Bot Setup
# -----------------------------
TOKEN = os.environ['DISCORD_TOKEN']          # Discord bot token
CHANNEL_ID = int(os.environ['DISCORD_CHANNEL'])  # Discord channel ID to send updates
SERVER_IP = os.environ['MC_SERVER_IP']       # Minecraft server IP (with optional port)

intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    print(f"Message received: {message.content} from {message.author}")
    if message.author == client.user:
        return
    if message.content.lower() == "!ping":
        await message.channel.send("Pong!")

# -----------------------------
# Minecraft Status Loop
# -----------------------------
async def server_status_loop():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    last_online = None
    while not client.is_closed():
        try:
            server = MinecraftServer.lookup(SERVER_IP)
            status = server.status()
            online = status.players.online
            if online != last_online:
                await channel.send(f"Players online: {online}")
                last_online = online
        except Exception:
            if last_online is not None:
                await channel.send("Server is offline!")
                last_online = None
        await asyncio.sleep(30)  # Check every 30 seconds

client.loop.create_task(server_status_loop())

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

Thread(target=run_flask).start()

# -----------------------------
# Start Discord Bot
# -----------------------------
client.run(TOKEN)
