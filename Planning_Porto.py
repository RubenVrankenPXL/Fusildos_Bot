import sys
import types

# --- FIX VOOR PYTHON 3.14 (AUDIOOP ERROR) ---
if 'audioop' not in sys.modules:
    dummy_audioop = types.ModuleType('audioop')
    sys.modules['audioop'] = dummy_audioop

import discord
from discord.ext import commands, tasks
from datetime import datetime, time, timezone
import random
import json
import os
from threading import Thread
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "Bot is online!"

def run_webserver():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_webserver)
    t.start()

# --- INSTELLINGEN ---
CHANNEL_ID = 1510031024799875233
GEHEUGEN_KANAAL_ID = 1510081681346920458  # ⚠️ PAS DIT AAN!

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True 

bot = commands.Bot(command_prefix="!", intents=intents)

async def laad_scores():
    channel = bot.get_channel(GEHEUGEN_KANAAL_ID)
    if channel:
        async for message in channel.history(limit=5):
            if message.author == bot.user and message.content.startswith("```json"):
                try:
                    return json.loads(message.content.replace("```json", "").replace("```", "").strip())
                except: pass
    return {}

async def sla_scores_op(scores):
    channel = bot.get_channel(GEHEUGEN_KANAAL_ID)
    if channel:
        async for message in channel.history(limit=10):
            if message.author == bot.user: await message.delete()
        await channel.send(f"```json\n{json.dumps(scores, indent=4)}\n```")

@bot.event
async def on_ready():
    print(f'--- {bot.user.name} is verbonden! ---')
    if not dagelijks_bericht.is_running():
        dagelijks_bericht.start()
        print("STATUS: Wekker gestart!")

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id or str(payload.emoji) != "🟢": return
    scores = await laad_scores()
    maand = datetime.now().strftime("%Y-%m")
    if maand not in scores: scores[maand] = {}
    uid = str(payload.user_id)
    scores[maand][uid] = scores[maand].get(uid, 0) + 1
    await sla_scores_op(scores)

@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id or str(payload.emoji) != "🟢": return
    scores = await laad_scores()
    maand = datetime.now().strftime("%Y-%m")
    uid = str(payload.user_id)
    if maand in scores and uid in scores[maand]:
        scores[maand][uid] = max(0, scores[maand][uid] - 1)
        await sla_scores_op(scores)

@tasks.loop(time=time(hour=10, minute=0, tzinfo=timezone.utc))
async def dagelijks_bericht():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        r = random.randint(69, 999)
        embed = discord.Embed(title="📅 Planning!", description=f"Kanaal: {r}\n🟢 = Aanwezig", color=discord.Color.blue())
        m = await channel.send(embed=embed)
        await m.add_reaction("🟢")

@bot.command()
async def testplan(ctx):
    r = random.randint(69, 999)
    m = await ctx.send(embed=discord.Embed(title="📅 Planning!", description=f"Kanaal: {r}\n🟢 = Aanwezig", color=discord.Color.blue()))
    await m.add_reaction("🟢")

@bot.command()
async def aanwezigheden(ctx, m_nr: str = None):
    scores = await laad_scores()
    doel = f"{datetime.now().year}-{m_nr}" if m_nr else datetime.now().strftime("%Y-%m")
    if doel not in scores: await ctx.send("Leeg!"); return
    res = sorted(scores[doel].items(), key=lambda x: x[1], reverse=True)
    tekst = ""
    for i, (uid, sc) in enumerate(res[:10], 1):
        mem = ctx.guild.get_member(int(uid)) or await ctx.guild.fetch_member(int(uid))
        naam = mem.display_name if mem else "Onbekend"
        tekst += f"**#{i}** {naam} — {sc}x aanwezig\n"
    await ctx.send(embed=discord.Embed(title="🏆 Overzicht", description=tekst, color=discord.Color.gold()))

@bot.command()
@commands.has_permissions(administrator=True)
async def resetleaderboard(ctx):
    await sla_scores_op({})
    await ctx.send("Gereset naar 0!")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    await ctx.message.delete()
    await ctx.channel.purge(limit=amount)
    msg = await ctx.send(f"🧹 {amount} gewist!")
    await msg.delete(delay=3)

keep_alive()
bot.run(os.getenv("DISCORD_TOKEN"))
