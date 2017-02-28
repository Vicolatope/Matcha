import re

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

def verify_verifyId(verify_id):
	if re.match('[^a-f0-9]', verify_id):
		return True
	return False

def verify_passwords(password, passconfirm):
	if re.search('[^a-zA-Z\d\s:]', password) is not None:
		return 'Don\'t use special chars in password'
	if len(password) < 6:
		return 'Password too short'
	if (re.search('[A-Z]', password) is None or
		re.search('[\d]', password) is None):
		return 'Pass must contain a capital and a number'
	if password != passconfirm:
		return 'Passwords are not the same'
	return None

def verify_create_form(email, password, passconfirm):
	error = verify_email(email)
	if error is not None:
		return error
	error = verify_passwords(password, passconfirm)
	return error

def verify_email(email):
	if re.match('^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email) is not None:
		return None
	else:
		return 'Invalid email'

def verify_post(message):
	if re.search('[^a-zA-Z.,!?\'"0-9\d\s:]', message) is not None:
		return 'Don\'t use special chars in message'
	return None

def verify_username(username):
	if len(username) < 6:
		return 'Username must contain 6 chars'
	if re.search('[^a-zA-Z\d\s:0-9]', username) is not None:
		return 'Don\'t use special chars in password'
	return None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS