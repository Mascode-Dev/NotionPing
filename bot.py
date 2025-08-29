import os
import dotenv
import discord
from discord.ext import commands, tasks
from database_models import DatabaseManager, NotionEvent, User
from datetime import datetime, timezone

dotenv.load_dotenv()

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())
db = DatabaseManager()

def get_name_by_notion_id(notion_id: str) -> str:
    session = db.get_session()
    try:
        user = session.query(User).filter_by(notion_id=notion_id).first()
        return user.name if user else "Inconnu"
    finally:
        session.close()

def create_event_embed(event: NotionEvent) -> discord.Embed:
    # Choix de couleur selon le statut
    if event.status == "Payant":
        color = discord.Color.red()  # Payant → rouge
        price_text = f"{event.price}€"
    elif event.status == "Libre":
        color = discord.Color.orange()  # Payant → orange
        price_text = f"??? €"
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
    embed.set_footer(text=f"Créé par {get_name_by_notion_id(event.created_by) or 'Inconnu'}")
    return embed

@client.event
async def on_ready():
    print("Bot initialisé.")
    try:
        synced = await client.tree.sync()
        print(f"✓ Commandes synchronisées: {len(synced)}")
    except Exception as e:
        print(f"✗ Échec de la synchronisation des commandes: {e}")


@client.tree.command(name="event", description="Return the last Notion event")
async def event(interaction: discord.Interaction):
    session = db.get_session()
    try:
        last_event = session.query(NotionEvent).order_by(NotionEvent.date.desc()).first()
        if last_event:
            embed = create_event_embed(last_event)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Aucun événement trouvé.")
    except Exception as e:
        print(f"✗ Erreur lors de la récupération de l'événement: {e}")
        await interaction.response.send_message("Une erreur s'est produite lors de la récupération de l'événement.")

@client.tree.command(name="register", description="Register a new user in the database")
async def register(interaction: discord.Interaction, notion_id: str, member: discord.Member):
    session = db.get_session()
    try:
        # Vérifier si l'utilisateur existe déjà
        existing_user = session.query(User).filter_by(notion_id=notion_id).first()
        if existing_user:
            await interaction.response.send_message("Cet utilisateur est déjà enregistré.")
            return

        # Ajouter le nouvel utilisateur
        db.add_user(
            name=interaction.user.name,
            discord_id=str(member.id),
            notion_id=notion_id,
            created_at=datetime.now(timezone.utc),
            updated_at=None
        )
        await interaction.response.send_message("Utilisateur enregistré avec succès.")
    except Exception as e:
        print(f"✗ Erreur lors de l'enregistrement de l'utilisateur: {e}")
        await interaction.response.send_message("Une erreur s'est produite lors de l'enregistrement de l'utilisateur.")
    finally:
        session.close()


client.run(os.getenv("DISCORD_TOKEN"))