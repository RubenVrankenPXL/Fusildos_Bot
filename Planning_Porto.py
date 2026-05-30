import sys
import types

# --- FIX VOOR PYTHON 3.14 (AUDIOOP ERROR) ---
if 'audioop' not in sys.modules:
    dummy_audioop = types.ModuleType('audioop')
    sys.modules['audioop'] = dummy_audioop

import asyncio
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone
import random
import json
import os
from threading import Thread
from flask import Flask

app = Flask('')
@app.route('/')
def home(): return "Bot is online!"
Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()

# --- CONFIG ---
CHANNEL_ID = 1510031024799875233
GEHEUGEN_KANAAL_ID = 1510081681346920458 # PAS DIT AAN!

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True 
bot = commands.Bot(command_prefix="!", intents=intents)

# --- WEKKER TAAK ---
@tasks.loop(minutes=1)
async def check_tijd():
    nu = datetime.now(timezone.utc)
    if nu.hour == 10 and nu.minute == 0:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            r = random.randint(69, 999)
            embed = discord.Embed(
                title="📅 Planning voor Vandaag!",
                description=f"Wie is er aanwezig? Reageer met de emoji's hieronder!\n\n"
                            f"📻 **Porto-kanaal van de dag:** Kanaal {r}\n\n"
                            f"🟢 = Aanwezig\n🔴 = Afwezig",
                color=discord.Color.blue()
            )
            m = await channel.send(embed=embed)
            await m.add_reaction("🟢")
            await m.add_reaction("🔴")
            await asyncio.sleep(61)

@bot.event
async def on_ready():
    print(f'--- {bot.user.name} is online! ---')
    if not check_tijd.is_running():
        check_tijd.start()
        print("STATUS: Wekker is succesvol gestart binnen on_ready!")

# --- COMMANDO'S ---
@bot.command()
async def testplan(ctx):
    r = random.randint(69, 999)
    m = await ctx.send(embed=discord.Embed(title="📅 Planning voor Vandaag!", description=f"Kanaal: {r}\n🟢 = Aanwezig\n🔴 = Afwezig", color=discord.Color.blue()))
    await m.add_reaction("🟢")
    await m.add_reaction("🔴")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    await ctx.message.delete()
    await ctx.channel.purge(limit=amount)

bot.run(os.getenv("DISCORD_TOKEN"))
