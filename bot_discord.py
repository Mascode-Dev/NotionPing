import discord
from discord.ext import commands, tasks
from database_models import DatabaseManager, NotionEvent
from dotenv import load_dotenv
import os


# ------------------------
# ⚙️ Config
# ------------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN or TOKEN == "None":
    raise ValueError("DISCORD_TOKEN is not set or invalid. Please check your .env file.")
print("Token:", TOKEN)  # juste pour vérifier qu'il est bien récupéré

CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
print("Channel ID:", CHANNEL_ID)  # juste pour vérifier qu'il est bien récupéré

print("--------------------------------------------------------------------------------------")





# ------------------------
# 🤖 Discord Bot
# ------------------------
intents = discord.Intents.default()
intents.message_content = True  # 🔑 essentiel pour lire les commandes
bot = commands.Bot(command_prefix="!", intents=intents)

# Init DB Manager (utilise les variables d'environnement DB_*)
db = DatabaseManager()

@bot.event
async def on_ready():
    print(f"{bot.user} est connecté ✅")
    send_event.start()  # lancer la tâche répétée

# ------------------------
# 📌 Tâche répétée toutes les 15 minutes
# ------------------------
@tasks.loop(minutes=15)
async def send_event():
    session = db.get_session()
    try:
        event = session.query(NotionEvent).order_by(NotionEvent.date.desc()).first()
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            if event:
                message = (
                    f"📢 **Nouvel événement**\n"
                    f"**Titre** : {event.title}\n"
                    f"**Description** : {event.description or 'Aucune'}\n"
                    f"**Date** : {event.date.strftime('%d/%m/%Y %H:%M') if event.date else 'Non précisée'}\n"
                    f"**Prix** : {event.price if event.price else 'Gratuit'}"
                )
            else:
                message = "Pas d'événement la chef..."
            await channel.send(message)
    finally:
        session.close()

# ------------------------
# Commande manuelle : !event
# ------------------------
@bot.command()
async def event(ctx):
    """Afficher le dernier événement Notion"""
    session = db.get_session()
    try:
        event = session.query(NotionEvent).order_by(NotionEvent.date.desc()).first()
        if event:
            message = (
                f"📌 **Dernier événement**\n"
                f"**Titre** : {event.title}\n"
                f"**Date** : {event.date.strftime('%d/%m/%Y %H:%M') if event.date else 'Non précisée'}"
            )
        else:
            message = "Pas d'événement la chef..."
        await ctx.send(message)
    finally:
        session.close()

bot.run(TOKEN)

print("fini :)")
