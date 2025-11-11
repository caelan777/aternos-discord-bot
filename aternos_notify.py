import os
import discord
import asyncio
from mcstatus import JavaServer
from flask import Flask
from threading import Thread

# -----------------------------
# Discord Bot Setup
# -----------------------------
TOKEN = os.environ['DISCORD_TOKEN']  # Make sure this env variable is set in Render
CHANNEL_ID = int(os.environ.get("DISCORD_CHANNEL", 0))  # Discord channel for updates
SERVER_IP = os.environ.get("MC_SERVER_IP", "play.example.com")  # Minecraft server IP
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 60))  # Seconds between server checks

intents = discord.Intents.default()
intents.messages = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    # Start background server status task
    client.loop.create_task(monitor_server())

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.lower() == "!ping":
        await message.channel.send("Pong!")

# -----------------------------
# Server Monitoring Logic
# -----------------------------
async def monitor_server():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if channel is None:
        print(f"Channel ID {CHANNEL_ID} not found!")
        return

    last_status = None
    while not client.is_closed():
        try:
            server = JavaServer(SERVER_IP)
            status = server.status()
            msg = f"Server online! {status.players.online}/{status.players.max} players."
            if last_status != msg:
                await channel.send(msg)
                last_status = msg
        except Exception as e:
            msg = f"Server offline or unreachable."
            if last_status != msg:
                await channel.send(msg)
                last_status = msg

        await asyncio.sleep(CHECK_INTERVAL)

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
