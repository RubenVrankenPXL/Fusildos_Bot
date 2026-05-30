import sys
import types
import asyncio
import discord
from discord.ext import commands, tasks
from datetime import datetime, timezone
import random
import json
import os
from threading import Thread
from flask import Flask

# --- FIX ---
if 'audioop' not in sys.modules:
    sys.modules['audioop'] = types.ModuleType('audioop')

app = Flask('')
@app.route('/')
def home(): return "Bot is online!"
Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()

# --- CONFIG ---
CHANNEL_ID = 1510031024799875233
GEHEUGEN_KANAAL_ID = 1234567890123456 # PAS AAN

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True 
bot = commands.Bot(command_prefix="!", intents=intents)

# --- LOGICA ---
async def laad_scores():
    channel = bot.get_channel(GEHEUGEN_KANAAL_ID)
    if not channel: return {}
    async for m in channel.history(limit=5):
        if m.author == bot.user and m.content.startswith("```json"):
            return json.loads(m.content.replace("```json", "").replace("```", "").strip())
    return {}

async def sla_scores_op(scores):
    channel = bot.get_channel(GEHEUGEN_KANAAL_ID)
    if not channel: return
    async for m in channel.history(limit=10):
        if m.author == bot.user: await m.delete()
    await channel.send(f"```json\n{json.dumps(scores, indent=4)}\n```")

@bot.event
async def on_ready():
    print(f'--- {bot.user.name} is online! ---')
    if not check_tijd.is_running(): check_tijd.start()

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
            await asyncio.sleep(61) # Zorgt dat hij niet dubbel stuurt

# --- COMMANDO'S ---
@bot.command()
async def testplan(ctx):
    r = random.randint(69, 999)
    embed = discord.Embed(
        title="📅 Planning voor Vandaag!",
        description=f"Wie is er aanwezig? Reageer met de emoji's hieronder!\n\n"
                    f"📻 **Porto-kanaal van de dag:** Kanaal {r}\n\n"
                    f"🟢 = Aanwezig\n🔴 = Afwezig",
        color=discord.Color.blue()
    )
    m = await ctx.send(embed=embed)
    await m.add_reaction("🟢")
    await m.add_reaction("🔴")

@bot.command()
async def afwezigen(ctx):
    async for m in ctx.channel.history(limit=5):
        if m.author == bot.user and any(str(r.emoji) == "🔴" for r in m.reactions):
            afwezigen_lijst = []
            for reaction in m.reactions:
                if str(reaction.emoji) == "🔴":
                    async for user in reaction.users():
                        if user != bot.user: afwezigen_lijst.append(user.display_name)
            await ctx.send(f"❌ **Afwezigen:** {', '.join(afwezigen_lijst) if afwezigen_lijst else 'Niemand is afwezig!'}")
            return
    await ctx.send("Geen planning gevonden.")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    await ctx.message.delete()
    await ctx.channel.purge(limit=amount)

bot.run(os.getenv("DISCORD_TOKEN"))
