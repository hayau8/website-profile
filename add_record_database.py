from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import SocketIO, emit, join_room
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta

from sqlalchemy.orm import aliased

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.permanent_session_lifetime = timedelta(days=7)
socketio = SocketIO(app)

# Konfiguracja SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat_app2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modele bazy danych
class User(db.Model):
    userID = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(24), nullable=False, unique=True)
    password = db.Column(db.String(30), nullable=False)
    timestamp = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())


class Room(db.Model):
    roomID = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user1 = db.Column(db.Integer, db.ForeignKey('user.userID'), nullable=False)
    user2 = db.Column(db.Integer, db.ForeignKey('user.userID'), nullable=False)


class Message(db.Model):
    messageID = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Integer, db.ForeignKey('user.userID'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    room_id = db.Column(db.Integer, db.ForeignKey('room.roomID'), nullable=False)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # new_room = User(username='hayau2', password='hayauP')
        # db.session.add(new_room)
        # db.session.commit()
        # user = User.query.all()
        messages = (Message.query
                    .filter_by(room_id=2)
                    .join(User, Message.username == User.userID)
                    .add_columns(User.username, Message.message, Message.timestamp)
                    .order_by(Message.timestamp.desc())
                    .limit(50)
                    .all())
        # Alias dla tabeli User
        user1_alias = aliased(User)  # Alias dla user1
        user2_alias = aliased(User)  # Alias dla user2

        # Zapytanie z join i add_columns
        cow = (Room.query
                 .join(user1_alias, Room.user1 == user1_alias.userID)  # Join dla user1
                 .join(user2_alias, Room.user2 == user2_alias.userID)  # Join dla user2
                 .add_columns(
            user1_alias.username.label('user1_username'),  # Nazwa dla user1
            user2_alias.username.label('user2_username'),  # Nazwa dla user2
            Room.roomID,
            Room.name
        )
                 .all())

        for i in cow:
            print(i.user1_username, i.user2_username)