import discord

# Remplace par le token de ton bot
TOKEN = "MTQxMDMyOTMwNTEzNjg5NDA5Mg.GhxXZd.b9HoxQwg3ZkfUwB0gPJCUYShzDW3RAIkFc4ilI"
""

# Remplace par l'ID du canal Discord où tu veux envoyer ton message
CHANNEL_ID =  "https://discord.com/channels/1089276816981766194/1410316625353244805" 

# Création du bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} est connecté !")

    # Récupérer le canal
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("Salut ! Je suis un bot 🤖")
    else:
        print("Canal introuvable.")

bot.run(TOKEN)
