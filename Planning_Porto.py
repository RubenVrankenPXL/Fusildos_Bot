import sys
import types
import asyncio
import discord
from discord.ext import commands, tasks
from datetime import datetime, time, timezone
import random
import json
import os
from threading import Thread
from flask import Flask

# --- FIX VOOR PYTHON 3.14 (AUDIOOP ERROR) ---
if 'audioop' not in sys.modules:
    dummy_audioop = types.ModuleType('audioop')
    sys.modules['audioop'] = dummy_audioop

app = Flask('')
@app.route('/')
def home(): return "Bot is online!"
Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()

# --- INSTELLINGEN ---
CHANNEL_ID = 1510031024799875233
GEHEUGEN_KANAAL_ID = 1510081681346920458  # ⚠️ PAS DIT AAN!

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True 
bot = commands.Bot(command_prefix="!", intents=intents)

# --- FUNCTIES ---
async def laad_scores():
    channel = bot.get_channel(GEHEUGEN_KANAAL_ID)
    if channel:
        async for m in channel.history(limit=5):
            if m.author == bot.user and m.content.startswith("```json"):
                return json.loads(m.content.replace("```json", "").replace("```", "").strip())
    return {}

async def sla_scores_op(scores):
    channel = bot.get_channel(GEHEUGEN_KANAAL_ID)
    if channel:
        async for m in channel.history(limit=10):
            if m.author == bot.user: await m.delete()
        await channel.send(f"```json\n{json.dumps(scores, indent=4)}\n```")

@bot.event
async def on_ready():
    print(f'--- {bot.user.name} is verbonden! ---')
    if not check_tijd.is_running(): check_tijd.start()

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

# --- WEKKER: PLANNING VANDAAG ---
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
            await asyncio.sleep(60)

# --- COMMANDO'S ---
@bot.command()
async def testplan(ctx):
    r = random.randint(69, 999)
    m = await ctx.send(embed=discord.Embed(title="📅 Planning voor Vandaag!", description=f"Wie is er aanwezig? Reageer met de emoji's hieronder!\n\n📻 **Porto-kanaal van de dag:** Kanaal {r}\n\n🟢 = Aanwezig\n🔴 = Afwezig", color=discord.Color.blue()))
    await m.add_reaction("🟢")
    await m.add_reaction("🔴")

@bot.command()
async def aanwezigheden(ctx, m_nr: str = None):
    scores = await laad_scores()
    doel = f"{datetime.now().year}-{m_nr}" if m_nr else datetime.now().strftime("%Y-%m")
    if doel not in scores: await ctx.send("Leeg!"); return
    res = sorted(scores[doel].items(), key=lambda x: x[1], reverse=True)
    tekst = "".join([f"**#{i}** {(ctx.guild.get_member(int(uid)) or await ctx.guild.fetch_member(int(uid))).display_name} — {sc}x aanwezig\n" for i, (uid, sc) in enumerate(res[:10], 1)])
    await ctx.send(embed=discord.Embed(title="🏆 Aanwezigheid Overzicht", description=tekst, color=discord.Color.gold()))

@bot.command()
async def afwezigen(ctx):
    async for m in ctx.channel.history(limit=5):
        if any(r.emoji == "🔴" for r in m.reactions):
            afwez = [ (await reaction.users().flatten()) for reaction in m.reactions if str(reaction.emoji) == "🔴" ]
            # Vereenvoudigd:
            users = [u.display_name async for u in next((r.users() for r in m.reactions if str(r.emoji) == "🔴"), []) if u != bot.user]
            await ctx.send(f"❌ **Afwezigen:** {', '.join(users) if users else 'Iedereen is aanwezig!'}")
            return
    await ctx.send("Geen planning gevonden.")

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

bot.run(os.getenv("DISCORD_TOKEN"))
