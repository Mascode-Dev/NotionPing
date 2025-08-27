"""
Script pour créer les tables PostgreSQL avec SQLAlchemy
"""
from dotenv import load_dotenv
from database_models import DatabaseManager
import os

# Charger les variables d'environnement
load_dotenv(dotenv_path=".env")

def create_tables():
    """Créer toutes les tables de la base de données"""
    try:
        print("🚀 Initialisation de la base de données...")
        
        # Vérifier les variables d'environnement
        required_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ Variables manquantes: {', '.join(missing_vars)}")
            return False
        
        # Afficher les informations de connexion (sans le mot de passe)
        print(f"📍 Connexion à: {os.getenv('DB_HOST')}:{os.getenv('DB_PORT', '5432')}")
        print(f"🗄️  Base de données: {os.getenv('DB_NAME')}")
        print(f"👤 Utilisateur: {os.getenv('DB_USER')}")
        
        # Créer le gestionnaire et les tables
        db_manager = DatabaseManager()
        db_manager.create_tables()
        
        print("✅ Tables créées avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des tables: {e}")
        return False


if __name__ == "__main__":
    
    response = input("\n🤔 Voulez-vous créer ces tables? (y/n): ")
    if response.lower() in ['y', 'yes', 'oui', 'o']:
        success = create_tables()
        if success:
            print("\n🎉 Base de données prête à utiliser!")
        else:
            print("\n😞 Échec de la création des tables")
    else:
        print("❌ Création annulée")
