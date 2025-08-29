import os
import dotenv
import discord
from discord.ext import commands, tasks
from database_models import DatabaseManager, NotionEvent, User
from datetime import datetime, timezone
import discord.ui
from notion_data import get_notion_events

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

def get_discord_id_by_notion(notion_id):
    session = db.get_session()
    try:
        user = session.query(User).filter_by(notion_id=notion_id).first()
        return user.discord_id if user else None
    finally:
        session.close()

def first_paragraph(desc, max_length=300):
    para = desc.split('\n')[0]
    if len(para) > max_length:
        return para[:max_length].rsplit(' ', 1)[0] + "..."
    return para

def short_description(desc, max_length=300):
    if len(desc) > max_length:
        # Coupe à la fin du mot et ajoute "..."
        return desc[:max_length].rsplit(' ', 1)[0] + "..."
    return desc

def parse_datetime(value: str):
    if not value:
        return None
    try:
        # si le format est ISO 8601 (ex: "2025-09-01T18:00:00.000Z")
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None

def dict_to_notion_event(event: dict) -> NotionEvent:
    notion_id = event['id']
    created_by = event['created_by']['id']
    created_at = event['created_time']

    archived = event['archived']
    title = event['properties']['Name']['title'][0]['text']['content']
    description = event['properties']['Description']['rich_text'][0]['text']['content'] if event['properties']['Description']['rich_text'] else None
    price = event['properties']['Prix']['number']
    date = event['properties']['Date']['date']['start']

    participant = []
    for person in event['properties']['Participants']['people']:
        participant.append(person['id'])
        
    status = event['properties']['Type']['status']['name']
    updated_at = event['last_edited_time']

    duration = event['properties']['Durée']['rich_text'][0]['text']['content'] if event['properties']['Durée']['rich_text'] else None
    location = event['properties']['Lieu']['rich_text'][0]['text']['content'] if event['properties']['Lieu']['rich_text'] else None
    limit_date = event['properties']['Date limite choix de participation']['date']['start'] if event['properties']['Date limite choix de participation']['date'] else None
    
    return NotionEvent(
        notion_id = notion_id,
        created_by = created_by,
        created_at = parse_datetime(created_at),
        archived = archived,
        title = title,
        description = description,
        price = price,
        date = parse_datetime(date),

        participant = participant,
        status = status,
        updated_at = parse_datetime(updated_at),
        duration = duration,
        location = location,
        limit_date = parse_datetime(limit_date)
    )


def create_event_embed(event: NotionEvent, mention: bool = False) -> discord.Embed:
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
        description=short_description(event.description or "Aucune description"),
        title=f"📢 {event.title or 'Pas de titre'}",
        
        color=color,
        timestamp=event.date if event.date else None  # timestamp de l'événement
    )
    # Ajouter un @everyone si mention == true

    embed.add_field(name="\u200b", value="\u200b", inline=False)
    
    # Date principale
    embed.add_field(
        name="📅 Date",
        value=event.date.strftime('%A %d %B %Y à %Hh%M').capitalize() if event.date else "Non précisée",
        inline=False
    )
    
    # Lieu
    if event.location:
        embed.add_field(
            name="📍 Lieu",
            value=f"{short_description(event.location, 100)}",
            inline=False
        )
    # Prix
    embed.add_field(
        name="💵 Prix",
        value=price_text,
        inline=False
    )
    # Date limite
    if event.limit_date:
        embed.add_field(
            name="⏳ Date limite d'inscription",
            value=event.limit_date.strftime('%A %d %B %Y à %Hh%M').capitalize(),
            inline=False
        )
    embed.set_footer(text=f"Créé par {get_name_by_notion_id(event.created_by) or 'Inconnu'}")
    return embed

class ParticipationView(discord.ui.View):
    def __init__(self, event=None):
        super().__init__(timeout=None)
        self.event_id = event.notion_id
        self.price = event.price
        self.created_by = event.created_by
        self.status = event.status

    @discord.ui.button(label="Participer", style=discord.ButtonStyle.success, custom_id="participate_btn")
    async def participate(self, interaction: discord.Interaction, button: discord.ui.Button):
        db.update_participant_to_event(self.event_id, interaction.user.id)
        if self.status == "Payant":
            mention = f"<@{get_discord_id_by_notion(self.created_by)}>" if self.created_by else "l'organisateur"
            await interaction.response.send_message("✅ Participation enregistrée !\nN'oublie pas d'envoyer {}€ à {}.".format(self.price, mention), ephemeral=True)
        else:
            await interaction.response.send_message("✅ Participation enregistrée !", ephemeral=True)

    @discord.ui.button(label="Refuser", style=discord.ButtonStyle.danger, custom_id="refuse_btn")
    async def refuse(self, interaction: discord.Interaction, button: discord.ui.Button):
        db.delete_participant_from_event(self.event_id, interaction.user.id)
        await interaction.response.send_message("❌ Participation refusée.", ephemeral=True)
        

@client.event
async def on_ready():
    print("Bot initialisé.")
    if not check_new_events.is_running():
        check_new_events.start()
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
            view = ParticipationView(event=last_event)
            await interaction.response.send_message(embed=embed, view=view)
        else:
            await interaction.response.send_message("Aucun événement trouvé.")
    except Exception as e:
        print(f"✗ Erreur lors de la récupération de l'événement: {e}")
        await interaction.response.send_message("Une erreur s'est produite lors de la récupération de l'événement.")
    finally:
        session.rollback()  # explicite
        session.close()

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
            name=member.name,
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

@tasks.loop(seconds=10)
async def check_new_events():
    session = db.get_session()
    try:
        # events existants en DB
        events = session.query(NotionEvent).all()
        notion_id_list = [event.notion_id for event in events]
        

        # nouveaux events depuis Notion (JSON brut)
        notion_data = get_notion_events()

        for event_data in notion_data['results']:
            notion_id = event_data.get("id")
            print("Notion list", notion_id_list)
            print(notion_id)
            if notion_id not in notion_id_list:
                event = dict_to_notion_event(event_data)  # conversion dict → objet SQLAlchemy (non persisté)

                embed = create_event_embed(event, mention=True)
                channel = client.get_channel(int(os.getenv("DISCORD_CHANNEL_ID")))
                view = ParticipationView(event=event)
                # await channel.send(content="@everyone", embed=embed, view=view)
                await channel.send(embed=embed, view=view)
                session.add(event)
                session.commit()

    except Exception as e:
        print(f"✗ Erreur lors de la vérification des nouveaux événements: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()


client.run(os.getenv("DISCORD_TOKEN"))