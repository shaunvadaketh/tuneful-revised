import os.path
import json

from flask import request, Response, url_for, send_from_directory
from werkzeug.utils import secure_filename
from jsonschema import validate, ValidationError

from . import models
from . import decorators
from tuneful import app
from .database import session
from .utils import upload_path



@app.route('/api/songs', methods=['GET'])
@decorators.accept("application/json")
def get_songs():
    data = session.query(models.Song)

    data = data.order_by(models.Song.id)
    return Response(json.dumps([song.as_dictionary() for song in data]),
                    200, mimetype='application/json')
                    

@app.route("/api/songs/<int:id>", methods=["GET"])
@decorators.accept("application/json")
def get_song(id):
    
    song = session.query(models.Song).get(id)

    
    if not song:
        message = "Song with id {} does not exist".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")

    
    data = json.dumps(song.as_dictionary())
    return Response(data, 200, mimetype="application/json")



@app.route("/api/songs", methods=["POST"])
@decorators.accept("application/json")
@decorators.require("application/json")
def post_song():
    
    data = request.json

    file = session.query(models.File).get(data['file']['id'])
    if not file:
        message = 'No file exists with id {}'.format(data['file']['id'])
        error = json.dumps({'message': message})
        return Response(error, 404, mimetype='application/json')

    song = models.Song(file_id=file.id)
    session.add(song)
    session.commit()

    data = json.dumps(song.as_dictionary())
    headers = {"Location": url_for("get_songs", id=song.id)}
    return Response(data, 201, headers=headers,
                    mimetype="application/json")

@app.route("/api/songs/<int:id>", methods = ["PUT"])
@decorators.accept("application/json")
@decorators.require("application/json")
def song_edit(id):
    
    song = session.query(models.Song).get(id)
    if not song:
        message = "Could not find song with id {}".format(id)
        error = json.dumps({"message": message})
        return Response(error, 404, mimetype="application/json")
        
    data = request.json
    song.file_id = data["file"]["id"]
    session.commit()
    
    data = json.dumps(song.as_dictionary())
    headers = {"Location": url_for("get_song", id=song.id)}
    return Response(data, 200, headers=headers,
                    mimetype="application/json")
                    

@app.route("/api/songs/<int:id>", methods=["DELETE"])
@decorators.accept("application/json")
def delete_song(id):
    song = session.query(models.Song).get(id)
    if not song:
        message = "Could not find song with id {}".format(id)
        data = json.dumps({"message": message})
        return Response(data, 404, mimetype="application/json")

    
    session.delete(song)
    session.commit()

    message = "Song with id {} was deleted".format(id)
    data = json.dumps({"message": message})
    return Response(data, 200, mimetype="application/json")
    
@app.route("/uploads/<name>", methods=["GET"])
def uploaded_file(name):
    return send_from_directory(upload_path(), name)
    
@app.route("/api/files", methods=["POST"])
@decorators.require("multipart/form-data")
@decorators.accept("application/json")
def file_post():
    import pdb; pdb.set_trace()
    file = request.files.get("file")
    #print (request)
    if not file:
        data = {"message": "Could not find file data"}
        return Response(json.dumps(data), 422, mimetype="application/json")

    filename = secure_filename(file.name)
    db_file = models.File(name=filename)
    session.add(db_file)
    session.commit()
    file.save(upload_path(filename))

    data = db_file.as_dictionary()
    return Response(json.dumps(data), 201, mimetype="application/json")