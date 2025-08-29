import os
import dotenv
import discord
from discord.ext import commands

dotenv.load_dotenv()

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())

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
    await interaction.response.send_message("Voici le dernier événement Notion.")

client.run(os.getenv("DISCORD_TOKEN"))