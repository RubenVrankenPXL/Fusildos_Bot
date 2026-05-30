import sys
import types

# 1. AUDIOOP FIX (MOET ALTIJD BOVENAAN)
if 'audioop' not in sys.modules:
    sys.modules['audioop'] = types.ModuleType('audioop')

# 2. ALLE IMPORTS
import asyncio
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone
import random
import json
import os
from threading import Thread
from flask import Flask

# 3. WEB SERVER VOOR RENDER
app = Flask('')
@app.route('/')
def home(): return "Bot is online!"
Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()

# 4. BOT CONFIGURATIE
CHANNEL_ID = 1510031024799875233
GEHEUGEN_ID = 1510081681346920458

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True 
bot = commands.Bot(command_prefix="!", intents=intents)

# 5. SCORES & FUNCTIES
async def update_score(user_id, change):
    channel = bot.get_channel(GEHEUGEN_ID)
    if not channel: return
    scores = {}
    async for m in channel.history(limit=1):
        if m.author == bot.user:
            try: scores = json.loads(m.content)
            except: pass
            await m.delete()
    scores[str(user_id)] = scores.get(str(user_id), 0) + change
    await channel.send(json.dumps(scores))

# 6. EVENTS
@bot.event
async def on_ready():
    print(f'--- {bot.user.name} is online! ---')
    if not check_tijd.is_running(): check_tijd.start()

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id or str(payload.emoji) != "🟢": return
    await update_score(payload.user_id, 1)

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id or str(payload.emoji) != "🟢": return
    await update_score(payload.user_id, -1)

# 7. WEKKER
@tasks.loop(minutes=1)
async def check_tijd():
    nu = datetime.now(timezone.utc)
    if nu.hour == 10 and nu.minute == 0:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            r = random.randint(69, 999)
            m = await channel.send(f"📅 **Planning voor vandaag!**\n📻 **Porto-kanaal:** {r}\n\n🟢 = Aanwezig\n🔴 = Afwezig")
            await m.add_reaction("🟢")
            await m.add_reaction("🔴")
            await asyncio.sleep(61)

# 8. COMMANDO'S
@bot.command()
async def testplan(ctx):
    r = random.randint(69, 999)
    m = await ctx.send(f"📅 **Planning voor vandaag!**\n📻 **Porto-kanaal:** {r}\n\n🟢 = Aanwezig\n🔴 = Afwezig")
    await m.add_reaction("🟢")
    await m.add_reaction("🔴")

@bot.command(name="aanwezigheden")
async def aanwezigheden(ctx):
    channel = bot.get_channel(GEHEUGEN_ID)
    if not channel: return
    async for m in channel.history(limit=1):
        try:
            s = json.loads(m.content)
            res = "\n".join([f"<@{uid}>: {sc}x" for uid, sc in s.items()])
            await ctx.send(f"🏆 **Totaal aanwezig:**\n{res}")
        except: await ctx.send("Geen scores gevonden.")

# 9. DEZE REGEL MOET ALS LAATSTE
bot.run(os.getenv("DISCORD_TOKEN"))
