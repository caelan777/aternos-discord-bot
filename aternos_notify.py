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
CHANNEL_ID = int(os.environ.get('DISCORD_CHANNEL', 1234567890))  # Discord channel ID

intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)

# Minecraft server domain (no port needed for Aternos)
MC_SERVER = os.environ.get("MC_SERVER", "example.aternos.me")
server = JavaServer.lookup(MC_SERVER)

async def check_server_status():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    last_status = None

    while not client.is_closed():
        try:
            status = server.status()
            msg = f"🟢 Server is online with {status.players.online}/{status.players.max} players!"
            if last_status != status.players.online:
                await channel.send(msg)
                last_status = status.players.online
        except Exception:
            if last_status is not None:
                await channel.send("🔴 Server is offline!")
                last_status = None

        await asyncio.sleep(60)  # Check every minute

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}')
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("🤖 Bot is now online and monitoring the server!")
    client.loop.create_task(check_server_status())

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.lower() == "!ping":
        await message.channel.send("🏓 Pong!")

# -----------------------------
# Flask Web Server (for Render keep-alive)
# -----------------------------
app = Flask(__name__)

@app.route("/healthz")
def health_check():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

Thread(target=run_flask).start()
client.run(TOKEN)

