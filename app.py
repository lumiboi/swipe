import sys
import subprocess

def install_and_import(package):
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

for pkg in ["flask", "flask_socketio", "eventlet"]:
    install_and_import(pkg)

from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room, emit
import os

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "secret")
socketio = SocketIO(app, cors_allowed_origins="*")

usernames = {}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/room/<room_id>")
def room(room_id):
    return render_template("room.html", room_id=room_id)

@socketio.on("join")
def handle_join(data):
    room = data["room"]
    username = data.get("username", "Anonim")
    usernames[request.sid] = username
    join_room(room)
    emit("user-joined", {"sid": request.sid, "username": username}, to=room, skip_sid=request.sid)

@socketio.on("signal")
def handle_signal(data):
    room = data["room"]
    emit("signal", {**data, "sid": request.sid}, to=room, skip_sid=request.sid)

@socketio.on("chat")
def handle_chat(data):
    room = data["room"]
    msg = data["msg"]
    username = data.get("username", usernames.get(request.sid, "Anonim"))
    emit("chat", {"sid": request.sid, "msg": msg, "username": username}, to=room)

@socketio.on("get-users")
def handle_get_users(data):
    room = data["room"]
    # O anki tüm kullanıcıların sid'ını ekrana paylaşan kişiye bildir
    for sid in socketio.server.manager.rooms["/"].get(room, set()):
        if sid != request.sid:
            emit("user-joined", {"sid": sid, "username": usernames.get(sid, "Anonim")}, room=request.sid)

@socketio.on("disconnect")
def handle_disconnect():
    usernames.pop(request.sid, None)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port)
