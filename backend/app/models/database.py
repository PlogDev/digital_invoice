"""
SQLAlchemy Models für PostgreSQL
Ersetzt die bisherigen SQLite-Models
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()

# Neue Kategorie-Struktur
class Kategorie(Base):
    __tablename__ = 'kategorien'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    beschreibung = Column(String(255))
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    unterkategorien = relationship("Unterkategorie", back_populates="kategorie", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Kategorie(id={self.id}, name='{self.name}')>"

class Unterkategorie(Base):
    __tablename__ = 'unterkategorien'
    
    id = Column(Integer, primary_key=True)
    kategorie_id = Column(Integer, ForeignKey('kategorien.id'), nullable=False)
    name = Column(String(100), nullable=False)
    beschreibung = Column(String(255))
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    kategorie = relationship("Kategorie", back_populates="unterkategorien")
    dokumente = relationship("Dokument", back_populates="unterkategorie")
    
    def __repr__(self):
        return f"<Unterkategorie(id={self.id}, name='{self.name}')>"

# Erweiterte Dokument-Tabelle
class Dokument(Base):
    __tablename__ = 'dokumente'
    
    id = Column(Integer, primary_key=True)
    dateiname = Column(String(255), nullable=False)
    kategorie_id = Column(Integer, ForeignKey('kategorien.id'))
    unterkategorie_id = Column(Integer, ForeignKey('unterkategorien.id'))
    pfad = Column(String(500), nullable=False)
    inhalt_vorschau = Column(Text)
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    metadaten = Column(JSON)  # PostgreSQL JSON Support!
    
    # Relationships
    unterkategorie = relationship("Unterkategorie", back_populates="dokumente")
    lieferscheine_extern = relationship("LieferscheinExtern", back_populates="dokument", cascade="all, delete-orphan")
    lieferscheine_intern = relationship("LieferscheinIntern", back_populates="dokument", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Dokument(id={self.id}, dateiname='{self.dateiname}')>"

# Metadatenfelder (bleibt fast gleich)
class MetadatenFeld(Base):
    __tablename__ = 'metadaten_felder'
    
    id = Column(Integer, primary_key=True)
    feldname = Column(String(100), unique=True, nullable=False)
    beschreibung = Column(String(255))
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<MetadatenFeld(id={self.id}, feldname='{self.feldname}')>"

# Umbenannte Lieferschein-Strukturen
class LieferscheinExtern(Base):
    __tablename__ = 'lieferscheine_extern'
    
    id = Column(Integer, primary_key=True)
    lieferscheinnummer = Column(String(100), unique=True, nullable=False)
    dokument_id = Column(Integer, ForeignKey('dokumente.id'), nullable=False)
    csv_importiert = Column(Boolean, default=False)
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    dokument = relationship("Dokument", back_populates="lieferscheine_extern")
    chargen_einkauf = relationship("ChargenEinkauf", back_populates="lieferschein_extern", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<LieferscheinExtern(id={self.id}, nummer='{self.lieferscheinnummer}')>"

class LieferscheinIntern(Base):
    __tablename__ = 'lieferscheine_intern'
    
    id = Column(Integer, primary_key=True)
    lieferscheinnummer = Column(String(100), unique=True, nullable=False)
    dokument_id = Column(Integer, ForeignKey('dokumente.id'), nullable=False)
    csv_importiert = Column(Boolean, default=False)
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    dokument = relationship("Dokument", back_populates="lieferscheine_intern")
    chargen_verkauf = relationship("ChargenVerkauf", back_populates="lieferschein_intern", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<LieferscheinIntern(id={self.id}, nummer='{self.lieferscheinnummer}')>"

# Umbenannte Chargen-Tabellen
class ChargenEinkauf(Base):
    __tablename__ = 'chargen_einkauf'
    
    id = Column(Integer, primary_key=True)
    lieferschein_extern_id = Column(Integer, ForeignKey('lieferscheine_extern.id'), nullable=False)
    
    # Bestehende CSV-Felder (von lieferschein_datensaetze)
    linr = Column(String(50))
    liname = Column(String(100))
    name1 = Column(String(100))
    belfd = Column(String(50))
    tlnr = Column(String(50))
    auart = Column(String(50))
    aftnr = Column(String(100))
    aps = Column(String(50))
    absn = Column(String(50))
    atnr = Column(String(100))
    artikel = Column(String(255))
    materialnr = Column(String(100))
    urlnd = Column(String(10))
    wartarnr = Column(String(20))
    menge = Column(String(50))
    erfmenge = Column(String(50))
    gebindeme = Column(String(50))
    snnr = Column(String(100))
    snnralt = Column(String(100))
    einzelek = Column(String(50))
    lieferscheinnr = Column(String(100))
    lieferdatum = Column(String(20))
    renrex = Column(String(100))
    redat = Column(String(20))
    bidser = Column(String(100))
    bid = Column(String(100))
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    lieferschein_extern = relationship("LieferscheinExtern", back_populates="chargen_einkauf")
    
    def __repr__(self):
        return f"<ChargenEinkauf(id={self.id}, artikel='{self.artikel}')>"

# Neue Chargen-Verkauf Tabelle
class ChargenVerkauf(Base):
    __tablename__ = 'chargen_verkauf'
    
    id = Column(Integer, primary_key=True)
    lieferschein_intern_id = Column(Integer, ForeignKey('lieferscheine_intern.id'), nullable=False)
    
    # Neue CSV-Struktur für Verkauf
    kdnr = Column(String(50))
    kdname = Column(String(100))
    vaart = Column(String(50))
    vtlfd = Column(String(50))
    aftnrkunde = Column(String(100))
    tlnr = Column(String(50))
    aps = Column(String(50))
    absn = Column(String(50))
    vtlfdra = Column(String(50))  # **markiert
    aftnrra = Column(String(100))  # **markiert
    artikel = Column(String(255))
    atnr = Column(String(100))
    materialnr = Column(String(100))
    urlnd = Column(String(10))
    wartarnr = Column(String(20))
    kdartnr = Column(String(100))
    menge = Column(String(50))
    megebinde = Column(String(50))
    charge = Column(String(100))  # **markiert
    einzelvk = Column(String(50))  # **markiert
    poswert = Column(String(50))
    lieferscheinnr = Column(String(100))
    lieferdatum = Column(String(20))
    renr = Column(String(100))
    redat = Column(String(20))
    bidsre = Column(String(100))
    bid = Column(String(100))
    bidsfo = Column(String(100))
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    lieferschein_intern = relationship("LieferscheinIntern", back_populates="chargen_verkauf")
    
    def __repr__(self):
        return f"<ChargenVerkauf(id={self.id}, artikel='{self.artikel}')>"