import os.path




from tuneful import app
from .database import Base, engine, session



from flask import url_for
from sqlalchemy import Column, Integer, String, Sequence, ForeignKey
from sqlalchemy.orm import backref, relationship


class Song(Base):
    __tablename__ = 'songs'

    id = Column(Integer, primary_key=True)
    file_id = Column(Integer, ForeignKey('files.id'))
    

    def as_dictionary(self):
        songfile = session.query(File).get(self.file_id)
        song = {
            'id': self.id,
            'file': {
                'id': songfile.id,
                'name': songfile.name
                }
        
        }
        return song


class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    song = relationship("Song", uselist=False, backref="song")

    def as_dictionary(self):
        return {
            'id': self.id,
            'name': self.name,
            "path": url_for("uploaded_file", name=self.name)
    }
            
        
        

