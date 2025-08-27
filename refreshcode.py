import os
import requests
import discord
from dotenv import load_dotenv
import json
import schedule
import time


def refresh_every_15_minutes(function):
    schedule.every(15).minutes.do(function)

    # Boucle infinie pour exécuter les tâches planifiées
    while True:
        schedule.run_pending()
        time.sleep(1)  # éviter de surcharger le CPU



refresh_every_15_minutes()




load_dotenv(dotenv_path=".env")


