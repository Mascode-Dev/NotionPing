"""
Modèles SQLAlchemy pour la base de données PostgreSQL
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import JSONB
import os

Base = declarative_base()

class NotionEvent(Base):
    """Modèle pour stocker les événements de Notion"""
    __tablename__ = 'notion_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    notion_id = Column(String(255), unique=True, nullable=False)  # ID depuis Notion
    created_by = Column(String(255))  # Utilisateur ayant créé l'événement
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    archived = Column(Boolean, default=False)  # État d'archivage de l'événement
    title = Column(String(500), nullable=False)
    description = Column(Text)
    price = Column(Integer)  # Prix de l'événement
    date = Column(DateTime)
    participant = Column(JSONB)  # Correction: utiliser JSONB au lieu de JSON
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f"<NotionEvent(id={self.id}, title='{self.title}', date='{self.date}')>"

class User(Base):
    """Modèle pour stocker les utilisateurs"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)  # Nom du mec
    discord_id = Column(String(255), unique=True, nullable=False)  # ID Discord
    notion_id = Column(String(255), unique=True, nullable=False)  # ID Notion
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<User(id={self.id}, discord_id='{self.discord_id}', name='{self.name}', notion_id='{self.notion_id}')>"

class DatabaseManager:
    """Gestionnaire de base de données avec SQLAlchemy"""
    
    def __init__(self, db_url=None):
        if db_url is None:
            # Construire l'URL de la base de données à partir des variables d'environnement
            db_host = os.getenv("DB_HOST", "localhost")
            db_port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_NAME")
            db_user = os.getenv("DB_USER")
            db_password = os.getenv("DB_PASSWORD")
            
            if not all([db_name, db_user, db_password]):
                raise ValueError("Les variables d'environnement DB_NAME, DB_USER, et DB_PASSWORD sont requises")
            
            db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        self.engine = create_engine(db_url, echo=True)  # echo=True pour voir les requêtes SQL
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Créer toutes les tables"""
        Base.metadata.create_all(bind=self.engine)
        print("✓ Tables créées avec succès")
    
    def get_session(self):
        """Obtenir une session de base de données"""
        return self.SessionLocal()
    
    def add_notion_event(self, notion_id, title, description=None, event_date=None):
        """Ajouter un nouvel événement Notion"""
        session = self.get_session()
        try:
            # Vérifier si l'événement existe déjà
            existing = session.query(NotionEvent).filter_by(notion_id=notion_id).first()
            if existing:
                # Mettre à jour l'événement existant
                existing.title = title
                existing.description = description
                existing.date = event_date  # Correction: utiliser 'date' au lieu de 'event_date'
                existing.updated_at = datetime.now(timezone.utc)
                session.commit()
                print(f"✓ Événement mis à jour: {title}")
                return existing
            else:
                # Créer un nouvel événement
                new_event = NotionEvent(
                    notion_id=notion_id,
                    title=title,
                    description=description,
                    date=event_date  # Correction: utiliser 'date' au lieu de 'event_date'
                )
                session.add(new_event)
                session.commit()
                print(f"✓ Nouvel événement ajouté: {title}")
                return new_event
        except Exception as e:
            session.rollback()
            print(f"✗ Erreur lors de l'ajout de l'événement: {e}")
            raise
        finally:
            session.close()
    
    def get_all_events(self):
        """Récupérer tous les événements"""
        session = self.get_session()
        try:
            events = session.query(NotionEvent).filter_by(is_active=True).all()
            return events
        finally:
            session.close()
    
    def get_events_by_date_range(self, start_date=None, end_date=None):
        """Récupérer les événements dans une plage de dates"""
        session = self.get_session()
        try:
            query = session.query(NotionEvent).filter_by(is_active=True)
            
            if start_date:
                query = query.filter(NotionEvent.date >= start_date)  # Correction: utiliser 'date'
            
            if end_date:
                query = query.filter(NotionEvent.date <= end_date)  # Correction: utiliser 'date'
            
            return query.all()
        finally:
            session.close()