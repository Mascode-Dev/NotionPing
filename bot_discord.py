import discord
from discord import app_commands
from discord.ext import tasks
from database_models import DatabaseManager, NotionEvent, User
from dotenv import load_dotenv
import os

# ------------------------
# ⚙️ Config
# ------------------------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN or TOKEN == "None":
    raise ValueError("DISCORD_TOKEN is not set or invalid. Please check your .env file.")
print("Token:", TOKEN)

CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
print("Channel ID:", CHANNEL_ID)


GUILD_ID = int(os.getenv("DISCORD_GUILD_ID")) 
print("Guild ID:", GUILD_ID)
# ------------------------
# 🤖 Discord Bot
# ------------------------
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

# Init DB Manager
db = DatabaseManager()

# ------------------------
# Événement on_ready
# ------------------------
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)

    # Sync uniquement sur ton serveur → instantané
    await tree.sync(guild=guild)

    print(f"{bot.user} est connecté ✅ (slash commands synchronisées sur {GUILD_ID})")

    # Optionnel : lancer ta tâche répétée
    # send_event.start()

    # Changer le status
    await bot.change_presence(activity=discord.Game(name="NotionPing"))




# ------------------------
# Commande register
# ------------------------


    # Fonction Python qui écrit en base
def register_user(discord_id, notion_id, user_name):
    session = db.get_session()
    try:
        existing_user = session.query(User).filter_by(discord_id=discord_id).first()
        if existing_user:
            print(f"✗ L'utilisateur avec Discord ID {discord_id} existe déjà.")
            return existing_user
        
        db.add_user(
            discord_id=discord_id,
            notion_id=notion_id,
            name=user_name
        )
        print(f"✓ Nouvel utilisateur enregistré: {user_name} (Discord ID: {discord_id})")
        return 'ok'
    except Exception as e:
        session.rollback()
        print(f"✗ Erreur lors de l'enregistrement de l'utilisateur: {e}")
        raise
    finally:
        session.close()

# Commande slash
@tree.command(name="register", description="Enregistrer un utilisateur avec son ID Notion")
@app_commands.describe(notion_id="Votre ID utilisateur Notion", name="Votre nom")
async def register(interaction: discord.Interaction, notion_id: str, name: str):
    user = register_user(interaction.user.id, notion_id, name)
    if user:
        await interaction.response.send_message(f"Utilisateur enregistré: {user.name}")
    else:
        await interaction.response.send_message("Erreur lors de l'enregistrement.")


# ------------------------
# Fonction pour créer un embed d'événement
# ------------------------
def create_event_embed(event: NotionEvent) -> discord.Embed:
    # Choix de couleur selon le statut
    if event.status == "Payant":
        color = discord.Color.red()  # Payant → rouge
        price_text = f"{event.price} 💰"
    elif event.status == "Libre":
        color = discord.Color.orange()  # Payant → orange
        price_text = f"??? 💰"
    else:
        color = discord.Color.green()  # Gratuit → vert
        price_text = "Gratuit 🎉"

    embed = discord.Embed(
        description=event.description or "Aucune description",
        title=f"📢 {event.title or 'Pas de titre'}",
        
        color=color,
        timestamp=event.date if event.date else None  # timestamp de l'événement
    )
    embed.add_field(name="📅 Date", value=event.date.strftime('%d/%m/%Y %H:%M') if event.date else "Non précisée", inline=True)
    embed.add_field(name="💵 Prix", value=price_text, inline=True)
    embed.set_footer(text=f"Créé par {event.created_by or 'Inconnu'}")
    return embed

# # ------------------------
# # Tâche répétée toutes les 15 minutes
# # ------------------------
# @tasks.loop(minutes=15)
# async def send_event():
#     session = db.get_session()
#     try:
#         event = session.query(NotionEvent).order_by(NotionEvent.date.desc()).first()
#         channel = bot.get_channel(CHANNEL_ID)
#         if channel:
#             if event:
#                 embed = create_event_embed(event)
#                 await channel.send(embed=embed)
#             else:
#                 await channel.send("Pas d'événement la chef...")
#     finally:
#         session.close()

# ------------------------
# Slash command /event
# ------------------------
@tree.command(name="event", description="Afficher le dernier événement Notion")
async def event(interaction: discord.Interaction):
    session = db.get_session()
    try:
        event_obj = session.query(NotionEvent).order_by(NotionEvent.date.desc()).first()
        if event_obj:
            embed = create_event_embed(event_obj)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Pas d'événement la chef...")
    finally:
        session.close()

# ------------------------
# Lancer le bot
# ------------------------
bot.run(TOKEN)
