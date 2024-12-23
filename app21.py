from flask import Flask, render_template, request, session, redirect, url_for, flash, get_flashed_messages, jsonify
from flask_socketio import SocketIO, emit, join_room
from datetime import timedelta
from databaseFunction import (User, Room, Message,Friend,Follow,CommentProfile, db, search_user_table,
                              save_message, fetch_messages_for_room, create_room, fetch_rooms,
                              search_friend, search_follow, count_follow, count_followers,search_comment,search_friend_request,
                              friends_accept_reject,create_log)
from sqlalchemy.orm import aliased
import logging

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.permanent_session_lifetime = timedelta(days=7)
socketio = SocketIO(app)

# Konfiguracja logging (logi)
logging.basicConfig(
    level=logging.DEBUG,  # Określa poziom logowania (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Format logów
    handlers=[
        logging.FileHandler('logs/app.log'),  # Logi zapisywane w pliku app.log w folderze logs
        logging.StreamHandler()  # Logi także wyświetlane na konsoli
    ]
)


# Konfiguracja SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat_app2.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# db = SQLAlchemy(app)
db.init_app(app)

# Trasy aplikacji
@app.route('/')
def index():
    msg = ''
    flashed_messages = get_flashed_messages()
    if flashed_messages:
        msg = flashed_messages[0]  # Pobierz pierwszą wiadomość ( funkcja po pobraniu usuwa ją z "kolejki" )
    if 'username' in session:
        return redirect(url_for('rooms'))
    return render_template('index.html',msg=msg)


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if username and password:
        user = search_user_table(username)
        if user and user.password == password:
                session['username'] = user.username
                return redirect(url_for('rooms'))
    flash('Nieprawidłowe dane')  # Flash wiadomości do url_for('index')
    return redirect(url_for('index'))
@app.route('/register',methods=['POST','GET'])
def register():
    if request.method == "POST":
        password = request.form.get('password-register')
        passwordConfirm = request.form.get('password-register-confirmation')
        username = request.form.get('username')
        if not search_user_table(username):
            if password == passwordConfirm and password and passwordConfirm and username:
                new_user = User(username=username,password=password)
                db.session.add(new_user)
                db.session.commit()
                # flash('Zarejestrowano, można się zalogować')
                # return redirect(url_for('index'))
                msg = "Zarejestrowano, można się zalogować"
                return render_template('register.html', msg=msg)
            else:
                # flash('Wprowadzono nieprawidłowe dane')
                # return redirect(url_for('index'))
                msg="Wprowadzono nieprawidłowe dane"
                return render_template('register.html',msg=msg)
        else:
            msg = "Taki użytkownik już istnieje"
            return render_template('register.html', msg=msg)
    elif request.method == "GET":
        return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/rooms')
def rooms():
    if 'username' not in session:
        return redirect(url_for('index'))
    username = session['username']
    user_rooms = fetch_rooms(username)
    msg = ''
    flashed_messages = get_flashed_messages()
    if flashed_messages: # Bład że nie ma uzytkownika z którym chce ktos utworzyć pokój O ;
        msg = flashed_messages[0]  # P
    return render_template('rooms.html', username=username, rooms=user_rooms,msg=msg)

@app.route('/room/<int:room_id>')
def room(room_id):
    if 'username' not in session:
        return redirect(url_for('index'))
    user = search_user_table(session['username']).userID
    room = Room.query.filter(
        ((Room.user1 == user) | (Room.user2 == user)) & (Room.roomID == room_id)
    ).first()
    user1_alias = aliased(User)
    user2_alias = aliased(User)
    room2 = (Room.query
             .join(user1_alias, Room.user1 == user1_alias.userID)
             .join(user2_alias, Room.user2 == user2_alias.userID)
             .add_columns(
                 user1_alias.username.label('user1Username'),
                 user2_alias.username.label('user2Username'),
                 Room.roomID,
                 Room.name).filter(Room.roomID == room_id).first())
    if not room:
        return redirect(url_for('rooms'))
    messages = fetch_messages_for_room(room_id)
    return render_template('chat.html', username=session['username'], room_id=room_id, messages=messages,user1= room2.user1Username,user2 = room2.user2Username)

@app.route('/create_room', methods=['POST'])
def create_new_room():
    if 'username' not in session:
        return redirect(url_for('index'))
    user2 = search_user_table(request.form.get('user2'))
    if user2:
        user1 = session['username']
        if user1 != user2.username: # aby nie tworzyc pokoi z samym sobą
            room_id = create_room(user1, user2.username)
            return redirect(url_for('room', room_id=room_id))
    flash('Brak takiego użytkownika')
    return redirect(url_for('rooms'))



@app.route('/search_users', methods=['GET'])
def search_users():
    if 'username' not in session:
        return redirect(url_for('index'))
    query = request.args.get('q', '').strip()  # argument q
    if not query:
        return jsonify([])

    users = User.query.filter(User.username.ilike(f"%{query}%")).all()

    user_list = [{"userID": user.userID, "username": user.username} for user in users]
    return jsonify(user_list)

@app.route('/profile/<string:profilName>')
@app.route("/profile")
def profile(profilName=None):
    if 'username' not in session:
        return redirect(url_for('index'))
    if profilName is None:
        user = search_user_table(session["username"])  # dane uzytkownika profila
    else:
        user = search_user_table(profilName)  # dane uzytkownika profila
        if not user:
            return render_template("404.html")
    user2 = search_user_table(session['username']) # dane uzytkownika sesji
    username = user.username
    followNumber = count_follow(user)
    followers = count_followers(user)
    timeCreateProfil = user.timestamp
    aboutMe = user.aboutMe
    friendList = search_friend(user)
    followList = search_follow(user)
    commentList = search_comment(user)
    canIfollow = "Polubiony" if Follow.query.filter_by(userFollow=user.userID, follower=user2.userID).first() else "Polub"
    # sekcja z sprawdzaniem czy przyjaciel / oczekujacy / nieznajomy
    request_friend = Friend.query.with_entities(Friend.friendStatus).filter(((Friend.friendUser1 == user.userID) & (Friend.friendUser2== user2.userID)) | ((Friend.friendUser1==user2.userID) & (Friend.friendUser2==user.userID))).first()
    if request_friend:
        if request_friend.friendStatus == 0:
            canIMakeFriend = "Dodaj do znajomych"
        elif request_friend.friendStatus == 1:
            canIMakeFriend = "Znajomy"
        elif request_friend.friendStatus == 2:
            canIMakeFriend = "Oczekujący na akceptacje"
    else:
        canIMakeFriend = "Dodaj do znajomych"
    return render_template('profile.html',canIMakeFriend=canIMakeFriend,canIfollow=canIfollow,youUsername=user2.username,username=username,followers=followers,followNumber=followNumber,timeCreateProfil=timeCreateProfil,aboutMe=aboutMe,friendList=friendList,followList=followList,commentList=commentList)

@app.route('/follow',methods=["POST"])
def add_folow():
    data = request.get_json()
    user1 = search_user_table(data.get('user1')) # uzytkownik ktorego polubiam
    user2 = search_user_table(data.get('user2')) # ja , ktory polubiam
    check_follow = Follow.query.filter_by(userFollow=user1.userID, follower=user2.userID).first()
    if check_follow:
        db.session.delete(check_follow)
        db.session.commit()
        return jsonify([False,f"Usunieto polubienie uzytkownika:  {user1.username}"])
    else:
        addFollow = Follow(userFollow=user1.userID,follower=user2.userID)
        db.session.add(addFollow)
        db.session.commit()
        return jsonify([True,f"Polubiono uzytkownika: {user1.username}"])

@app.route("/friend",methods=["POST"])
def add_friend():
    data = request.get_json()
    whoSend = search_user_table(data.get('whoSend'))
    whoToSend = search_user_table(data.get("whoToSend"))
    check_friend = Friend.query.with_entities(Friend.friendStatus).filter(((Friend.friendUser1 == whoSend.userID) & (Friend.friendUser2 == whoToSend.userID)) | (
            (Friend.friendUser1 == whoToSend.userID) & (Friend.friendUser2 == whoSend.userID))).first()
    if check_friend.friendStatus == 0: # wyslanie zaproszenia
        answer = friends_accept_reject(whoSend, whoToSend, 2)
        return jsonify(["2","ZAPROSIŁEM CIE ZAAKCEPTUJ"])
    elif check_friend.friendStatus == 1: # usuniecie z znajomych
        answer = friends_accept_reject(whoSend, whoToSend, 0)
        return jsonify(["0","Usunałem cię :/"])
    elif  check_friend.friendStatus == 2: # wycofanie zaproszenia
        query = (Friend.query.with_entities(Friend.friendStatus, Friend.friendUser1, Friend.friendUser2).filter(
            (Friend.friendUser1 == whoToSend.userID) & (Friend.friendUser2 == whoSend.userID)).first()).friendStatus == 2
        if query: # wysyłanie zapytania czy osoba zapraszana nie wyslala juz zaproszenia, jezeli tak to dodaje do znajomych (akceptacja)
            answer = friends_accept_reject(whoSend, whoToSend, 1)
            return jsonify(["1","Nowy koliga"])
        answer = friends_accept_reject(whoSend, whoToSend, 0)
        return jsonify(["0","Zmieniłem zdanie, nie chce przyjaciół"])
    else:
        ask_friend = Friend(friendUser1=whoSend.userID, friendUser2=whoToSend.userID, friendStatus=2)
        db.session.add(ask_friend)
        db.session.commit()
        return jsonify(["2", "ZAPROSIŁEM CIE ZAAKCEPTUJ"])

@app.route('/comment',methods=["POST"])
def comment_profile():
    data = request.get_json()
    try:
        whoComment = search_user_table(data.get("whoComment"))
        whoGetComment = search_user_table(data.get("whoGetComment"))
        contentComment = str(data.get("contentComment"))
        if not all([whoComment,whoGetComment,contentComment]):
            return jsonify([False])
        sendComment = CommentProfile(commentText=contentComment,commentUser=whoComment.userID,commentUserProfile=whoGetComment.userID)
        db.session.add(sendComment)
        db.session.commit()
        return jsonify([True])
    except Exception as e:
        db.session.rollback()  # Wycofaj zmiany
        return jsonify([False])

@app.route("/friends",methods=["POST","GET"])
def friends():
    if "username" not in session:
        return redirect(url_for("index"))
    user = search_user_table(session["username"])
    if request.method=="GET":
        friendListRequest = search_friend_request(user)
        return render_template("friends_panel.html",friendListRequest=friendListRequest,user=user)
    elif request.method == "POST":
        data = request.get_json()
        user2 = search_user_table(data.get("user2"))
        decision = int(data.get("decision"))
        odpowiedz = friends_accept_reject(user,user2,decision)
        if odpowiedz == False:
            return jsonify([False],"Bład w zapytaniu")
        if decision == 0:
            return jsonify([False,"Nie chce przyjaciela"])
        elif decision==1:
            return jsonify([True,"Mam nowego p rzyjaciela"])
@app.errorhandler(404)
def app_handle(e):
    return render_template('404.html'),404

# WebSocket obsługa
@socketio.on('send_message')
def handle_message(data):
    room_id = data.get('room_id')
    message = data.get('message')
    username = session.get('username', 'Anonim')
    user = search_user_table(username)
    if room_id and message and user:
        save_message(user.userID, message, room_id)
        emit('receive_message', {'username': username, 'message': message}, room=room_id)

@socketio.on('join_room')
def join_room_event(data):
    room_id = data.get('room_id')
    if room_id:
        join_room(room_id)
        emit('status', {'msg': f'{session["username"]} joined room {room_id}'}, room=room_id)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
