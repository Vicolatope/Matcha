from flask import Flask, render_template, session, escape, request, redirect, url_for, flash, send_file
import re
import hashlib
import sys
import time
import datetime
import os
from threading import Lock
from User import User
from GDSession import GDSession
from flask_mail import Mail, Message
from inputVerify import *
from werkzeug.utils import secure_filename
import json
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)
mail = Mail(app)

socketConnections = {}
lock = Lock()

app.config.update(
	MAIL_SERVER='smtp.gmail.com',
	MAIL_PORT=465,
	MAIL_USE_SSL=True,
	MAIL_USERNAME='vicolatope@gmail.com',
	MAIL_PASSWORD='MatchaApp1',
	MAIL_DEFAULT_SENDER='matcha@gmail.com',
	SESSION_COOKIE_NAME='OUYIUOYHJ',
	UPLOAD_FOLDER='uploads')
mail = Mail(app)

def verify_generate(email):
	link = hashlib.sha224(email.encode(encoding='UTF-8')).hexdigest()
	print(link)
	return link

def check_connection():
	if session.get('logged_in') == True and session.get('verify') == None:
		return True
	return False

def send_verify_email(email, verify):
	message = Message("Hello", recipients=[email])
	message.html='Verify your account <a href="http://localhost:5000/verify/%s">here</a>' % verify
	mail.send(message)

'''
	------------- CHAT SOCKET ------------
'''


@socketio.on('chat_connection')
def handle_event(data):
	if check_connection() == False:
		return
	user = User(session.get('user_id'))
	lock.acquire()
	socketConnections.update({user.user_id: request.sid})
	print('socket : '+ str(socketConnections))
	lock.release()

@socketio.on('send_to')
def messageSender(data):
	user = User(session.get('user_id'))
	lock.acquire()
	if data['id'] in socketConnections:
		socketio.emit('received', {'message': data['content'], 'from': user.user_id}, room=socketConnections[data['id']])
		user.storeMessageTo(data['id'], data['content'])
	else:
		user.storeMessageTo(data['id'], data['content'])
	lock.release()
	print(data);



'''
	------------- APP ROUTES -------------
'''

#used to get all posts from the logged user
@app.route('/post_cheater')
def cheatPosts():
	user = User(session.get('user_id'))
	posts = render_template('posts.html', posts=user.getAllPosts())
	return posts

@app.route('/test')
def test():
	return json.dumps(User(session.get('user_id')).lastMessagesWith(38))

@app.route('/load_chat')
def loadChatResponder():
	if check_connection() == False:
		return 'error'
	user = User(session.get('user_id'))
	matches = user.getAllMatches()
	matches.append({'my_id': user.user_id})
	return json.dumps(matches)

#
@app.route('/get_searched_users')
def cheatUserSearchedPosts():
	user = User(session.get('user_id'))
	return render_template('home_posts.html', posts=user.getSearchedUsersPosts())

@app.route('/like_user/<int:user_id>')
def likeAUser(user_id):
	if check_connection() == False:
		return redirect(url_for('indexRoute'))
	user = User(session.get('user_id'))
	if user.likeUser(user_id) == True:
		return 'match'
	return 'OK'


@app.route('/')
def indexRoute():
	if check_connection() == True:
		user = User(session.get('user_id'))
		posts = user.getSearchedUsersPosts()
		return render_template('home.html', posts=posts)
	return render_template('signup.html')

@app.route('/edit_profile', methods=['POST'])
def editProfileHandler():
	if check_connection() != True:
		return redirect(url_for('indexRoute'))
	user = User(session.get('user_id'))
	for label in request.form:
		print('%s = %s' % (label, request.form[label]))
		if label not in ['username', 'email']:
			flash('You can not edit that you stupid')
			return redirect(url_for('profileRoute'))
		return user.updateProfile(label, request.form)

@app.route('/user/<int:user_id>')
def getUserProfile(user_id):
	if check_connection() == False:
		return redirect(url_for('indexRoute'))
	user = User(user_id)
	print(user_id)
	profilePic = user.getProfilePicture()
	print(profilePic)
	posts = user.getAllPosts()
	return render_template('user.html', posts=posts, username=user.username, profileImage=profilePic)



@app.route('/login', methods=['POST'])
def loginRoute():
	user = User()
	if session.get('logged_in') == True:
		flash('You\'re already logged in')
		return redirect(url_for('indexRoute'))
	if ('email' in request.form and
		'password' in request.form):
		email = request.form['email']
		password = request.form['password']
		if user.checkAccount(email, password) == False:
			flash('unknown user')
			return redirect(url_for('indexRoute'))
		session['logged_in'] = True
		session['user_id'] = user.user_id
		return redirect(url_for('indexRoute'))
	else:
		flash('Missing value')
		return redirect(url_for('indexRoute'))

@app.route('/image/<image_id>')
def getImage(image_id):
	if check_connection() == False:
		return redirect(url_for('indexRoute'))
	if os.path.exists('uploads/%s' % image_id):
		return send_file('uploads/%s' % image_id, mimetype='image/png')


@app.route('/get_user_posts')
def getImages():
	if check_connection() == False:
		return redirect(url_for('indexRoute'))
	user = User(session.get('user_id'))
	return json.dumps(user.getAllPosts())
	

@app.route('/logout')
def logoutRoute():
	if check_connection() == False:
		return redirect(url_for('indexRoute'))
	session['user'] = None
	session['logged_in'] = False
	return redirect(url_for('indexRoute'))

@app.route('/signup_success')
def waitVerifyRoute():
	return render_template('wait_verify.html')

@app.route('/finalize', methods=['POST'])
def finalizeRoute():
	if session.get('logged_in') == None or session.get('verify') == None:
		return redirect(url_for('indexRoute'))
	if ('photo' in request.files and
		'username' in request.form and
		'message' in request.form):
		username = request.form['username']
		message = request.form['message']
		photo = request.files['photo']
		if photo.filename == '':
			flash('No selected file')
			return redirect('/verify/%s' % session.get('verify'))
		error = verify_username(username)
		if error != None:
			flash(error)
			return redirect('/verify/%s' % session.get('verify'))
		if photo and allowed_file(photo.filename):
			filename = secure_filename(photo.filename)
			encoded = username + str(time.time())
			saveFilename = hashlib.sha224(encoded.encode()).hexdigest()
			photo.save(os.path.join(app.config['UPLOAD_FOLDER'], saveFilename))
			GDSession().run('MATCH (a:Person) WHERE a.verify = {verify} SET a.username = {username}, a.verify = NULL CREATE (a)-[:POSTED {at: {time}}]->(b:Post {content: {message}}), (b)-[:HAS_IMAGE]->(c:ImagePath {isProfile: true, storedAt: {image}})',
				{'verify': session.get('verify'), 'username': username, 'time': time.time(), 'message': message, 'image': saveFilename})
			session['verify'] = None
			return redirect(url_for('indexRoute'))
		else:
			flash('Problem uploading the file')
			return redirect('/verify/%s' % session.get('verify'))
	else:
		flash('Missing value')
		return redirect('/verify/%s' % session.get('verify'))

@app.route('/last_messages/<int:user_id>')
def getUserLastMessageRoute(user_id):
	if check_connection() == False:
		return redirect(url_for('indexRoute'))
	user = User(session.get('user_id'))
	try:
		messagesList = user.lastMessagesWith(user_id)
	except:
		messagesList = []
	return json.dumps(messagesList)

@app.route('/profile')
def profileRoute():
	if check_connection() == False:
		return redirect(url_for('indexRoute'))
	resImage = list(GDSession().run('MATCH (a:Person)-[:POSTED]->(c:Post)-[:HAS_IMAGE]->(b:ImagePath) WHERE ID(a) = {id} AND b.isProfile = true RETURN b.storedAt AS imagePath, a.email as email, a.username as username', {'id': session.get('user_id')}))
	return render_template('profile.html', profileImage='image/%s' % resImage[0]['imagePath'], title="Your profile", email=resImage[0]['email'], username=resImage[0]['username'])

@app.route('/verify/<verify_id>')
def verifyRoute(verify_id):
	if verify_verifyId(verify_id):
		return 'No Such User' #replace with a template ====>
	result = GDSession().run('MATCH (a:Person) WHERE a.verify = {verify} RETURN ID(a) AS id', {"verify": verify_id,})	
	res = list(result)
	if len(res) == 0:
		return 'No such user'
	session['verify'] = verify_id
	session['user_id'] = res[0]['id']
	session['logged_in'] = True
	return render_template('account_completion.html')
	

@app.route('/create', methods=['POST'])
def createRoute():
	# return json.dumps(request.form)
	if ('email' in request.form and
		'password' in request.form and
		'passconfirm' in request.form and
		'sex' in request.form and
		'search' in request.form and
		'firstname' in request.form and
		'lastname' in request.form and
		'birthdate' in request.form and
		'movies' in request.form and
		'music' in request.form and
		'food' in request.form and
		'bed' in request.form and
		'books' in request.form and
		'sport' in request.form):
		email = request.form['email']
		password = request.form['password']
		passconfirm = request.form['passconfirm']
		sex = request.form['sex']
		firstname = request.form['firstname']
		lastname = request.form['lastname']
		preference = request.form['search']
		likes = {'Music': request.form['music'], 'Movies': request.form['movies'], 'Books': request.form['books'], 'Sport': request.form['sport'], 'Bed': request.form['bed'], 'Food': request.form['food']}
		print(email)
		error = verify_create_form(email, password, passconfirm)
		if error is not None:
			return error
		try:
			birthdate = time.mktime(datetime.datetime.strptime(request.form['birthdate'], "%d/%m/%Y").timetuple())
			if (birthdate < 23652000):
				return 'You\'re too young for that !'
		except:
			return 'Wrong date format you should use dd/mm/yyyy'
		try:
			verify = verify_generate(email)
			idReturn = GDSession().run('CREATE (a:Person:%s {email: {email}, password: {password}, search: {preference}, verify: {verify}, birthdate:{birthdate}, firstname: {firstname}, lastname:{lastname}}) RETURN ID(a) AS id' % ('Woman' if sex == 'woman' else 'Man'),
				{'email' : email, 'password' : password, 'preference': preference, 'verify': verify, 'birthdate': birthdate, 'firstname': firstname, 'lastname': lastname})
			user_id = list(idReturn)[0]['id']
			for interest in likes:
				if likes[interest] == 'on':
					GDSession().run('MATCH (a:Person), (i:Interest) WHERE ID(a) = {user_id} AND i.name = {interestName} CREATE (a)-[c:LIKES]->(i)',
						{'user_id': user_id, 'interestName': interest})
				else:
					print('I dont like %s', likes[interest])
			send_verify_email(email, verify)
			return 'success'
		except Exception as e:
			return 'Email already used'
	else:
		return 'Missing values'

if __name__ == '__main__':
	socketio.run(app)

app.secret_key = 'IDUEWOWEUDH646ddw23357dew'