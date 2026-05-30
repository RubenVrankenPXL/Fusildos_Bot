import sys
import types

# --- FIX VOOR PYTHON 3.14 (AUDIOOP ERROR) ---
if 'audioop' not in sys.modules:
    dummy_audioop = types.ModuleType('audioop')
    sys.modules['audioop'] = dummy_audioop
# ---------------------------------------------

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

# --- INSTELLINGEN KANALEN ---
CHANNEL_ID = 1510031024799875233       # Je normale planningskanaal
GEHEUGEN_KANAAL_ID = 1510081681346920458  # ⚠️ VERVANG DIT door het ID van je geheime Discord-kanaal!

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True # Zorgt ervoor dat we server-bijnamen mogen ophalen

bot = commands.Bot(command_prefix="!", intents=intents)

# --- SLIM KANAAL-GEHEUGEN SYSTEM ---
async def laad_scores():
    channel = bot.get_channel(GEHEUGEN_KANAAL_ID)
    if channel:
        async for message in channel.history(limit=5):
            if message.author == bot.user and message.content.startswith("```json"):
                try:
                    schone_json = message.content.replace("```json", "").replace("```", "").strip()
                    return json.loads(schone_json)
                except:
                    pass
    return {}

async def sla_scores_op(scores):
    channel = bot.get_channel(GEHEUGEN_KANAAL_ID)
    if channel:
        async for message in channel.history(limit=10):
            if message.author == bot.user:
                await message.delete()
        json_tekst = json.dumps(scores, indent=4)
        await channel.send(f"```json\n{json_tekst}\n```")

@bot.event
async def on_ready():
    print(f'{bot.user.name} is online en de logica is waterdicht!')
    if not dagelijks_bericht.is_running():
        dagelijks_bericht.start()

# --- REACTIE TOEGEVOEGD (AANMELDEN) ---
@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    if str(payload.emoji) == "🟢":
        scores = await laad_scores()
        huidige_maand = datetime.now().strftime("%Y-%m")
        
        if huidige_maand not in scores:
            scores[huidige_maand] = {}
            
        user_id = str(payload.user_id)
        scores[huidige_maand][user_id] = scores[huidige_maand].get(user_id, 0) + 1
        
        await sla_scores_op(scores)

# --- REACTIE WEGGEHAALD (AFMELDEN) ---
@bot.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == bot.user.id:
        return

    if str(payload.emoji) == "🟢":
        scores = await laad_scores()
        huidige_maand = datetime.now().strftime("%Y-%m")
        user_id = str(payload.user_id)
        
        if huidige_maand in scores and user_id in scores[huidige_maand]:
            scores[huidige_maand][user_id] -= 1
            
            # Voorkom dat scores onder de 0 zakken
            if scores[huidige_maand][user_id] < 0:
                scores[huidige_maand][user_id] = 0
                
            await sla_scores_op(scores)

@tasks.loop(time=time(hour=10, minute=0, tzinfo=timezone.utc))
async def dagelijks_bericht():
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        random_kanaal = random.randint(69, 999)
        embed = discord.Embed(
            title="📅 Planning voor morgen!",
            description=f"Wie is er aanwezig? Reageer met de emoji's hieronder!\n\n"
                        f"📻 **Porto-kanaal van de dag:** Kanaal {random_kanaal}\n\n"
                        f"🟢 = Aanwezig\n🔴 = Niet aanwezig",
            color=discord.Color.blue()
        )
        bericht = await channel.send(embed=embed)
        await bericht.add_reaction("🟢")
        await bericht.add_reaction("🔴")

@bot.command()
async def testplan(ctx):
    random_kanaal = random.randint(69, 999)
    embed = discord.Embed(
        title="📅 Planning voor Vandaag!",
        description=f"Wie is er aanwezig? Reageer met de emoji's hieronder!\n\n"
                    f"📻 **Porto-kanaal van de dag:** Kanaal {random_kanaal}\n\n"
                    f"🟢 = Aanwezig\n🔴 = Niet aanwezig",
        color=discord.Color.blue()
    )
    bericht = await ctx.send(embed=embed)
    await bericht.add_reaction("🟢")
    await bericht.add_reaction("🔴")

# --- OPROEPEN AANWEZIGHEDEN (LEADERBOARD) ---
@bot.command()
async def aanwezigheden(ctx, maand_nummer: str = None):
    scores = await laad_scores()
    nu = datetime.now()
    
    if maand_nummer is None:
        doel_maand = nu.strftime("%Y-%m")
        maand_naam = nu.strftime("%B %Y")
    else:
        if len(maand_nummer) == 2 and maand_nummer.isdigit():
            doel_maand = f"{nu.year}-{maand_nummer}"
            try:
                datum_object = datetime.strptime(doel_maand, "%Y-%m")
                maand_naam = datum_object.strftime("%B %Y")
            except ValueError:
                await ctx.send("⚠️ **Fout:** Ongeldig maandnummer. Gebruik bijvoorbeeld `05` voor mei.")
                return
        else:
            await ctx.send("❌ **Oeps!** Gebruik: `!aanwezigheden` of `!aanwezigheden 05`")
            return

    if doel_maand not in scores or not scores[doel_maand]:
        await ctx.send(f"🏆 **Er zijn nog geen aanwezigheden bijgehouden voor {maand_naam}!**")
        return

    maand_scores = scores[doel_maand]
    gesorteerde_scores = sorted(maand_scores.items(), key=lambda item: item[1], reverse=True)
    
    leaderboard_tekst = ""
    for i, (user_id, score) in enumerate(gesorteerde_scores[:10], start=1):
        member = ctx.guild.get_member(int(user_id))
        if member is None:
            try:
                member = await ctx.guild.fetch_member(int(user_id))
            except:
                member = None

        if member:
            naam = member.display_name
        else:
            naam = f"Ex-lid ({user_id})"
        
        if i == 1: medaille = "🥇"
        elif i == 2: medaille = "🥈"
        elif i == 3: medaille = "🥉"
        else: medaille = f"**#{i}**"
        
        leaderboard_tekst += f"{medaille} **{naam}** — {score}x aanwezig\n"

    embed = discord.Embed(
        title=f"🏆 Aanwezigheid Overzicht ({maand_naam})",
        description=leaderboard_tekst,
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)

# --- RESET COMMANDO (Alleen voor Admins) ---
@bot.command()
@commands.has_permissions(administrator=True)
async def resetleaderboard(ctx):
    await sla_scores_op({})
    await ctx.send("🏆 **Alle aanwezigheden zijn succesvol gereset naar 0!**")

@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = 10):
    # Verwijder direct het commando-bericht van de gebruiker
    await ctx.message.delete()
    
    # Wis vervolgens de rest van de berichten
    await ctx.channel.purge(limit=amount)
    
    bevestiging = await ctx.send(f"🧹 **{amount} berichten succesvol gewist!**")
    await bevestiging.delete(delay=3)

@bot.event
async def on_ready():
    print(f'{bot.user.name} is online!')
    
    # Check of de taak al loopt, zo nee, start hem
    if not dagelijks_bericht.is_running():
        dagelijks_bericht.start()
        print("Wekker is succesvol aangezet!")
    else:
        print("Wekker liep al.")

keep_alive()
TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
