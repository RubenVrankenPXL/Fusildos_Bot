import discord
from discord.ext import commands, tasks
from datetime import datetime, time, timezone
import random
import json
import os

CHANNEL_ID = 1510031024799875233 
SCORES_FILE = "maand_leaderboard.json"

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)

def laad_scores():
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, "r") as f:
            return json.load(f)
    return {}

def sla_scores_op(scores):
    with open(SCORES_FILE, "w") as f:
        json.dump(scores, f, indent=4)

@bot.event
async def on_ready():
    print(f'{bot.user.name} is online en klaar voor de planning én het scorebord!')
    dagelijks_bericht.start()

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    if str(payload.emoji) == "🟢":
        scores = laad_scores()
        huidige_maand = datetime.now().strftime("%Y-%m")
        
        if huidige_maand not in scores:
            scores[huidige_maand] = {}
            
        user_id = str(payload.user_id)
        scores[huidige_maand][user_id] = scores[huidige_maand].get(user_id, 0) + 1
        
        sla_scores_op(scores)

@tasks.loop(time=time(hour=9, minute=0, tzinfo=timezone.utc))
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

@bot.command()
async def leaderboard(ctx, maand_nummer: str = None):
    scores = laad_scores()
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
            await ctx.send("❌ **Oeps!** Gebruik: `!leaderboard` of `!leaderboard 05`")
            return

    if doel_maand not in scores or not scores[doel_maand]:
        await ctx.send(f"🏆 **Leaderboard voor {maand_naam} is nog leeg!**")
        return

    maand_scores = scores[doel_maand]
    gesorteerde_scores = sorted(maand_scores.items(), key=lambda item: item[1], reverse=True)
    
    leaderboard_tekst = ""
    for i, (user_id, score) in enumerate(gesorteerde_scores[:10], start=1):
        user = bot.get_user(int(user_id))
        if user is None:
            try:
                user = await bot.fetch_user(int(user_id))
            except discord.NotFound:
                user = None

        naam = user.name if user else f"Onbekend ({user_id})"
        
        if i == 1: medaille = "🥇"
        elif i == 2: medaille = "🥈"
        elif i == 3: medaille = "🥉"
        else: medaille = f"**#{i}**"
        
        leaderboard_tekst += f"{medaille} {naam} — {score}x aanwezig\n"

    embed = discord.Embed(
        title=f"🏆 Aanwezigheid Leaderboard ({maand_naam})",
        description=leaderboard_tekst,
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)

TOKEN = os.getenv("DISCORD_TOKEN")
bot.run(TOKEN)
