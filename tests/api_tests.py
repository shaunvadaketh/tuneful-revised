import unittest
import os
import shutil
import json
try: from urllib.parse import urlparse
except ImportError: from urlparse import urlparse # Py2 compatibility
from io import StringIO
from io import BytesIO

import sys; print(list(sys.modules.keys()))
# Configure our app to use the testing databse
os.environ["CONFIG_PATH"] = "tuneful.config.TestingConfig"

from tuneful import app
from tuneful import models
from tuneful.utils import upload_path
from tuneful.database import Base, engine, session

class TestAPI(unittest.TestCase):
    """ Tests for the tuneful API """

    def setUp(self):
        """ Test setup """
        self.client = app.test_client()

        # Set up the tables in the database
        Base.metadata.create_all(engine)

        # Create folder for test uploads
        os.mkdir(upload_path())

    def tearDown(self):
        """ Test teardown """
        session.close()
        # Remove the tables and their data from the database
        Base.metadata.drop_all(engine)

        # Delete test upload folder
        shutil.rmtree(upload_path())

    def test_get_songs(self):
        fileA = models.File(name='fileA.mp3')
        songA = models.Song(file_id=fileA.id)
        fileB = models.File(name='fileB.mp3')
        songB = models.Song(file_id=fileB.id)

        session.add_all([fileA, fileB, songA, songB])
        session.commit()

        response = self.client.get(
            '/api/songs',
            headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, 'application/json')

        data = json.loads(response.data.decode('ascii'))
       

        SongA, SongB = data
        self.assertEqual(SongA['id'], songA.id)
        self.assertEqual(SongA['file_id'], songA.file_id)
        
        self.assertEqual(SongB['id'], songB.id)
        self.assertEqual(SongB['file_id'], songB.file_id)
        

    
    def test_post_song(self):
        fileA = models.File(name='fileA.mp3')
        session.add(fileA)
        session.commit()

        data = {
            "file": {
                "id": fileA.id
            }
        }

        response = self.client.post(
            "/api/songs",
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")
        self.assertEqual(
            urlparse(response.headers.get("Location")).path, "/api/songs")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["id"], 1)
        
        

        songs = session.query(models.Song).all()
        self.assertEqual(len(songs), 1)

        song = songs[0]
        self.assertEqual(song.id, 1)
        self.assertEqual(song.file_id, 1)
        
        
    def test_put_song(self):
        
        fileA = models.File(name='fileA.mp3')
        songA = models.Song(file_id = fileA.id)
        fileB = models.File(name='fileB.mp3')
        

        session.add_all([fileA, fileB, songA])
        session.commit()

        data = {
            "file": {
                "id": fileB.id
            }
        }

        response = self.client.put(
            "/api/songs/{}".format(songA.id),
            data=json.dumps(data),
            content_type="application/json",
            headers=[("Accept", "application/json")])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(data["id"], 1)
        
        

        songs = session.query(models.Song).all()
        self.assertEqual(len(songs), 1)

        song = songs[0]
        self.assertEqual(song.id, 1)
        self.assertEqual(song.file_id, 2)
        

    def test_delete_song(self):
        
        new_file = models.File(name='New_File')
        session.add(new_file)
        session.commit()
        new_song = models.Song(file_id=new_file.id)
        session.add(new_song)
        session.commit()

        response = self.client.delete(
            "/api/songs/{}".format(new_song.id),
            headers=[("Accept", "application/json")])

        session.delete(new_file)
        session.commit()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "application/json")

        songs = session.query(models.Song).all()
        self.assertEqual(len(songs), 0)
    
    def test_get_uploaded_file(self):
        path =  upload_path("test.txt")
        with open(path, "wb") as f:
            f.write(b"File contents")

        response = self.client.get("/uploads/test.txt")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/plain")
        self.assertEqual(response.data, b"File contents")
        
    def test_file_upload(self):
        data = {
            "file": (BytesIO(b"File contents"), "test.txt")
        }

        response = self.client.post("/api/files",
            data=data,
            content_type="multipart/form-data",
            headers=[("Accept", "application/json")]
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.mimetype, "application/json")

        data = json.loads(response.data.decode("ascii"))
        self.assertEqual(urlparse(data["path"]).path, "/uploads/test.txt")

        path = upload_path("test.txt")
        self.assertTrue(os.path.isfile(path))
        with open(path, "rb") as f:
            contents = f.read()
        self.assertEqual(contents, b"File contents")