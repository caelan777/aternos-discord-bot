from mcstatus import JavaServer
import discord
import asyncio
import os
# ===== CONFIGURATION =====
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = 1437560932942217306  # Your Discord channel ID
SERVER_ADDRESS = "TourtonneGarden.aternos.me"  # Aternos server
CHECK_INTERVAL = 180
# ==========================

intents = discord.Intents.default()
client = discord.Client(intents=intents)

was_online = False
last_players = set()

async def check_server_status():
    global was_online, last_players
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print("[ERROR] Could not find Discord channel. Check CHANNEL_ID.")
        return

    while not client.is_closed():
        try:
            # ⚡ Resolve the server fresh each iteration
            server = JavaServer.lookup(SERVER_ADDRESS)
            status = server.status()
            current_players = set(p.name for p in status.players.sample) if status.players.sample else set()

            # Server just came online
            if not was_online:
                player_list = ", ".join(current_players) if current_players else "No one"
                await channel.send(f"✅ Server is ONLINE! Players online: {player_list}")
                was_online = True
                last_players = current_players

            # Server is online, check for player changes
            else:
                added = current_players - last_players
                removed = last_players - current_players
                messages = []
                if added:
                    messages.append(f"🟢 Players joined: {', '.join(added)}")
                if removed:
                    messages.append(f"🔴 Players left: {', '.join(removed)}")
                if messages:
                    await channel.send("\n".join(messages))
                last_players = current_players

        except Exception as e:
            # Server offline or temporarily unreachable
            if was_online:
                await channel.send("❌ Server is OFFLINE!")
                was_online = False
                last_players = set()
            print(f"[DEBUG] Server offline or error: {e}")

        await asyncio.sleep(CHECK_INTERVAL)

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    client.loop.create_task(check_server_status())

client.run(TOKEN)
