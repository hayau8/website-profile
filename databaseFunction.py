from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import aliased
from sqlalchemy import func
import os
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    userID = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(24), nullable=False, unique=True)
    password = db.Column(db.String(30), nullable=False)
    timestamp = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())
    aboutMe = db.Column(db.Text,default="Użytkownik nic nie napisał",nullable=False)


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

class Follow(db.Model):
    followID = db.Column(db.Integer,primary_key = True)
    userFollow = db.Column(db.Integer, db.ForeignKey('user.userID'),nullable=False) # osoba polubiona
    follower = db.Column(db.Integer,db.ForeignKey('user.userID'),nullable=False) # polubiajacy osobe
    timeFollow = db.Column(db.TIMESTAMP,default=db.func.current_timestamp())

class Friend(db.Model):
    friendID = db.Column(db.Integer,primary_key=True)
    friendUser1 = db.Column(db.Integer,db.ForeignKey('user.userID'),nullable=False) # tutaj jest kto zainicjował zaproszenie
    friendUser2 = db.Column(db.Integer,db.ForeignKey('user.userID'),nullable=False) # ten kto ma zaakceptować czy coś :P
    friendStatus = db.Column(db.Integer,default = 0) # 0-Nie 1-Tak 2-Oczekiwanie
    timeFriend = db.Column(db.TIMESTAMP,default = db.func.current_timestamp())

class CommentProfile(db.Model):
    commentProfileID = db.Column(db.Integer,primary_key=True)
    commentText = db.Column(db.Text,nullable = False)
    commentUser = db.Column(db.Integer,db.ForeignKey('user.userID'),nullable=False)
    commentUserProfile = db.Column(db.Integer,db.ForeignKey('user.userID'),nullable=False)
    timecomment = db.Column(db.TIMESTAMP,default = db.func.current_timestamp())




# Funkcja do wyszukiwania użytkownika po nazwie
def search_user_table(username):
    return User.query.filter_by(username=username).first()

# Funkcje obsługi bazy danych
def save_message(username_id, message, room_id):
    try:
        new_message = Message(username=username_id, message=message, room_id=room_id)
        db.session.add(new_message)
        db.session.commit()
    except Exception as e:
        create_log(e)

def fetch_messages_for_room(room_id):
    try:
        messages = (Message.query
                    .filter_by(room_id=room_id)
                    .join(User, Message.username == User.userID)
                    .add_columns(User.username, Message.message, Message.timestamp)
                    .order_by(Message.timestamp.desc())
                    .limit(50)
                    .all())
        return messages[::-1]  # Odwrócenie kolejności dla starszych wiadomości
    except Exception as e:
        create_log(e)

def create_room(user1, user2):
    try:
        user1_obj = search_user_table(user1)
        user2_obj = search_user_table(user2)

        room = Room.query.filter(
            ((Room.user1 == user1_obj.userID) & (Room.user2 == user2_obj.userID)) |
            ((Room.user1 == user2_obj.userID) & (Room.user2 == user1_obj.userID))
        ).first()

        if not room:
            new_room = Room(name="Pokój rozmów", user1=user1_obj.userID, user2=user2_obj.userID)
            db.session.add(new_room)
            db.session.commit()
            return new_room.roomID
        return room.roomID
    except Exception as e:
        create_log(e)

def fetch_rooms(username):
    try:
        user = search_user_table(username)

        user1_alias = aliased(User)  # Alias dla user1
        user2_alias = aliased(User)  # Alias dla user2

        rooms = (Room.query
                 .join(user1_alias, Room.user1 == user1_alias.userID)  # Join dla user1
                 .join(user2_alias, Room.user2 == user2_alias.userID)  # Join dla user2
                 .add_columns(
                     user1_alias.username.label('user1Username'),  # Nazwa dla user1
                     user2_alias.username.label('user2Username'),  # Nazwa dla user2
                     Room.roomID,
                     Room.name).filter((Room.user1 == user.userID) | (Room.user2 == user.userID)
                                       ).all())

        return rooms
    except Exception as e:
        create_log(e)
    # user = search_user_table(username)
    # return Room.query.join(User,Room.user1 == User.userID).join(User, Room.user2 == User.userID).filter((Room.user1 == user.userID) | (Room.user2 == user.userID)).all()

def search_friend(user):
    try:
        user1_alias = aliased(User)  # Alias dla user1
        user2_alias = aliased(User)  # Alias dla user2
        friends = (Friend.query.with_entities(user1_alias.username.label('friend1Username'),user2_alias.username.label('friend2Username'),
                                Friend.timeFriend,Friend.friendID,Friend.friendStatus).join(user1_alias,Friend.friendUser1 == user1_alias.userID)
                .join(user2_alias,Friend.friendUser2 == user2_alias.userID)
                .filter(((Friend.friendUser1 == user.userID) | (Friend.friendUser2 == user.userID)) & (Friend.friendStatus == 1))
    ).all()

        return friends
    except Exception as e:
        create_log(e)

def search_friend_request(user):
    try:
        user1_alias = aliased(User)  # Alias dla user1
        user2_alias = aliased(User)  # Alias dla user2
        friends = (Friend.query.join(user1_alias,Friend.friendUser1 == user1_alias.userID)
                .join(user2_alias,Friend.friendUser2 == user2_alias.userID)
                .filter(((Friend.friendUser1 == user.userID) | (Friend.friendUser2 == user.userID)) & (Friend.friendStatus == 2))
                .with_entities(user1_alias.username.label('friend1Username'),user2_alias.username.label('friend2Username'),
                                Friend.timeFriend,Friend.friendID,Friend.friendStatus)).all()
        return friends
    except Exception as e:
        create_log(e)


def friends_accept_reject(user,user2,decision: int):
    # 0-Nie 1-Tak 2-Oczekiwanie
    try:
        conclusion = Friend.query.filter(((Friend.friendUser1==user.userID) & (Friend.friendUser2==user2.userID)) | ((Friend.friendUser1==user2.userID) & (Friend.friendUser2==user.userID))).update({"friendStatus": decision})
        db.session.commit()
        return True
    except Exception as e:
        create_log(e)
        return False

# .add_column(user1_alias.username.label('userFollow'),
#             user2_alias.username.label('follower'),
#             Follow.followID,
#             Follow.timeFollow,
#             func.count(Follow.followID).label("counts"))

def search_follow(user):
    try:
        user1_alias = aliased(User)  # Alias dla user1
        user2_alias = aliased(User)  # Alias dla user2
        follows = (Follow.query.join(user1_alias,Follow.follower == user1_alias.userID)
                .join(user2_alias,Follow.userFollow == user2_alias.userID)
                .filter((Follow.follower == user.userID))
                .with_entities(user1_alias.username.label('userFollow'), user2_alias.username.label('follower'),
                               Follow.followID,Follow.timeFollow,
                               )
                .all())
        return follows
    except Exception as e:
        create_log(e)

def count_follow(user):
    # userFollow to kogo osoba polubiła
    try:
        count_follows = (Follow.query.filter(Follow.userFollow == user.userID)
                         .with_entities(func.count(Follow.followID).label('row_count')).scalar())
        return count_follows
    except Exception as e:
        create_log(e)
def count_followers(user):
    try:
        count_followers = (Follow.query.filter(Follow.follower == user.userID)
                         .with_entities(func.count(Follow.followID).label('row_count')).scalar())
        return count_followers
    except Exception as e:
        create_log(e)

def search_comment(user):
    try:
        user1_alias = aliased(User)
        comments = (CommentProfile.query.join(user1_alias,CommentProfile.commentUserProfile==user1_alias.userID)
                    .join(User,CommentProfile.commentUser==User.userID)
                    .filter(CommentProfile.commentUserProfile==user.userID)
                    .with_entities(CommentProfile.commentText,CommentProfile.timecomment,User.username.label("commentUser"),user1_alias.username.label("commentUserProfile")).all())
        return comments
    except Exception as e:
        create_log(e)



def create_log(message):
    logs_folder = os.path.join(os.getcwd(), 'logs')
    log_file_path = os.path.join(logs_folder, 'app.log')
    if not os.path.exists(logs_folder):
        os.makedirs(logs_folder)
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = [f"[{current_time}] {i}\n" for i in message.split('\n')]
    with open(log_file_path, 'a', encoding='utf-8') as log_file:
        log_file.writelines(log_entry)