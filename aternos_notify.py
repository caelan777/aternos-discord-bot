import os
import discord
from mcstatus import JavaServer
from flask import Flask
from threading import Thread
import asyncio
import time
import requests
import traceback

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

# -----------------------------
# Async server status checker
# -----------------------------
async def check_server_status():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    last_state = None
    last_players = -1

    while not client.is_closed():
        try:
            server = JavaServer.lookup(MC_SERVER)
            status = server.status()
            is_online = True
            players_online = status.players.online
            players_max = status.players.max

            # only send if something changes
            if last_state != is_online or players_online != last_players:
                await channel.send(
                    f"✅ Server is online with {players_online}/{players_max} players."
                )
                last_state = is_online
                last_players = players_online

        except Exception as e:
            # Only send "offline" once until back online
            if last_state is not False:
                await channel.send("⚠️ Server appears to be offline or unreachable.")
                last_state = False
                last_players = -1

            # log detailed traceback so loop doesn’t silently die
            print("Error in check_server_status:", traceback.format_exc())

        await asyncio.sleep(60)  # wait 60 seconds before next check


@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    # Start the loop
    client.loop.create_task(check_server_status())


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.lower() == "!ping":
        await message.channel.send("🏓 Pong!")

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
# Self-ping to keep Render awake
# -----------------------------
def self_ping():
    url = "https://aternos-discord-bot-dh09.onrender.com/healthz"
    while True:
        try:
            requests.get(url, timeout=10)
            print("🔁 Pinged self to stay awake")
        except Exception as e:
            print("⚠️ Ping failed:", e)
        time.sleep(600)  # every 10 minutes

# -----------------------------
# Start everything
# -----------------------------
Thread(target=run_flask, daemon=True).start()
Thread(target=self_ping, daemon=True).start()

client.run(TOKEN)

