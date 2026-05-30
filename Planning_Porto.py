import sys
import types

# FIX: AUDIOOP MOET EERST
if 'audioop' not in sys.modules:
    sys.modules['audioop'] = types.ModuleType('audioop')

import asyncio
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone
import random
import json
import os
from threading import Thread
from flask import Flask

# Webserver om de bot wakker te houden
app = Flask('')
@app.route('/')
def home(): return "Bot is online!"
Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()

CHANNEL_ID = 1510031024799875233
GEHEUGEN_ID = 1510081681346920458

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True 
bot = commands.Bot(command_prefix="!", intents=intents)

# Functie om scores bij te werken met namen
async def update_score(user, change):
    channel = bot.get_channel(GEHEUGEN_ID)
    if not channel: return
    scores = {}
    async for m in channel.history(limit=1):
        if m.author == bot.user:
            try: scores = json.loads(m.content)
            except: pass
            await m.delete()
    
    # Sla op met naam (display_name)
    name = user.display_name
    scores[name] = scores.get(name, 0) + change
    await channel.send(json.dumps(scores))

@bot.event
async def on_ready():
    print(f'--- {bot.user.name} is online! ---')
    if not check_tijd.is_running(): check_tijd.start()

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id or str(payload.emoji) != "🟢": return
    member = payload.member
    await update_score(member, 1)

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id or str(payload.emoji) != "🟢": return
    # Haal de guild op om de member te vinden
    guild = bot.get_guild(payload.guild_id)
    member = await guild.fetch_member(payload.user_id)
    await update_score(member, -1)

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

@bot.command()
async def testplan(ctx):
    r = random.randint(69, 999)
    m = await ctx.send(f"📅 **Planning voor vandaag!**\n📻 **Porto-kanaal:** {r}\n\n🟢 = Aanwezig\n🔴 = Afwezig")
    await m.add_reaction("🟢")
    await m.add_reaction("🔴")

@bot.command(name="aanwezigheden")
async def aanwezigheden(ctx):
    channel = bot.get_channel(GEHEUGEN_ID)
    async for m in channel.history(limit=1):
        try:
            s = json.loads(m.content)
            res = "\n".join([f"{naam}: {sc}x" for naam, sc in s.items()])
            await ctx.send(f"🏆 **Totaal aanwezig:**\n{res}")
        except: await ctx.send("Nog geen aanwezigheden geregistreerd.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"✅ {amount} berichten verwijderd.", delete_after=3)

bot.run(os.getenv("DISCORD_TOKEN"))
