from GDSession import GDSession
from inputVerify import *
import time

class User():

	def __init__(self, user_id=None):
		if user_id != None:
			result = GDSession().run('MATCH (a:Person) WHERE ID(a) = {id} RETURN a.username AS username, a.search AS searches, labels(a) AS labels', {'id': user_id})
			for res in result:
				self._username = res['username']
				self._user_id = user_id
				self._search = res['searches']
				self._sex = 'Man' if 'Man' in res['labels'] else 'Woman'


	@property
	def user_id(self):
		return self._user_id

	@property
	def username(self):
		return self._username

	@user_id.setter
	def user_id(self, value):
		self._user_id = value

	def getAllPosts(self):
		print(self.user_id)
		result = GDSession().run('MATCH (a:Person)-[p:POSTED]->(c:Post) WHERE ID(a) = {id} OPTIONAL MATCH (c)-[i:HAS_IMAGE]->(d:ImagePath) RETURN ID(c) AS id, c.content as content, d.storedAt as imagePath ORDER BY p.at',
			{'id': self.user_id})
		print(type(result))
		print(result)
		res = []
		for item in result:
			if item['content'] != None:
				if 'imagePath' in item and item['imagePath'] != None:
					res.append({'id' : 'post_%s_%s' % (self.user_id, item['id']), 'content' : item['content'], 'image': item['imagePath']})
				else:
					res.append({'id' : 'post_%s_%s' % (self.user_id, item['id']), 'content' : item['content']})
		return res

	def updateProfile(self, label, form):
		error = verify_email(form[label]) if label == 'email' else verify_username(form[label])
		if error != None:
			return 'error'
		try:
			result = GDSession().run('MATCH (a:Person) WHERE ID(a) = {id} SET a.%s = {newValue} RETURN a.%s AS %s' % (label, label, label),
				{'label': label, 'id': self.user_id, 'newValue': form[label]})
			res = list(result);
			if len(res) == 0:
				flash('An error occured, couldn\'t edit profile')
				return 'error'
			print(res[0][label])
			return res[0][label]
		except:
			return 'error'

	def getProfilePicture(self):
		profilePicReq = GDSession().run('MATCH (a:Person)-[:POSTED]->(d:Post)-[:HAS_IMAGE]->(c:ImagePath) WHERE ID(a) = {id} and c.isProfile = true RETURN c.storedAt AS image',
			{'id': self._user_id})
		porfilePic = list(profilePicReq)
		if (len(porfilePic) == 0):
			return 'No picture'
		return porfilePic[0]['image']

	def checkAccount(self, email, password):
		result = GDSession().run('MATCH (a:Person) WHERE a.email = {email} AND a.password = {password} RETURN ID(a) AS id LIMIT 1',
			{'email': email, 'password': password})
		res = list(result)
		if (len(res) == 0):
			return False
		self._user_id = res[0]['id']
		self.__init__(self._user_id)
		print(self._search)
		return True

	def getSearchedUsersPosts(self):
		resList = []
		sex = 'Men' if self._sex == 'Man' else 'Women'
		result = GDSession().run('MATCH (a:Person:%s)-[p:POSTED]->(c:Post) WHERE a.search = {sex} AND ID(a) <> {id} OPTIONAL MATCH (c)-[:HAS_IMAGE]->(i:ImagePath) WHERE i.isProfile = true RETURN a.username as otherName, ID(c) as imageId, ID(a) as otherId, p.at as postime, c.content as content, i.storedAt as imagePath' % ('Man' if self._search == 'Men' else 'Woman'),
			{'sex': sex, 'id': self._user_id})
		for post in result:
			if post['imagePath'] != None:
				resList.append({'id': 'post_%s_%s' % (post['imageId'], post['otherId']), 'user_id': post['otherId'], 'username': post['otherName'], 'postedAt': post['postime'], 'content': post['content'], 'image': post['imagePath']})
			else:
				resList.append({'id': 'post_%s_%s' % (post['imageId'], post['otherId']), 'user_id': post['otherId'], 'username': post['otherName'], 'postedAt': post['postime'], 'content': post['content']})
		return resList

	def getAllMatches(self):
		resList = []
		result = GDSession().run('MATCH (a:Person)-[r:LIKED {match : true}]->(b:Person) WHERE ID(a) = {id} RETURN b.username AS username, ID(b) AS id',
			{'id': self._user_id})
		for match in result:
			resList.append({'username': match['username'], 'id': match['id']})
		return resList

	def lastMessagesWith(self, other_id):	
		resList = []
		result = GDSession().run('MATCH (a:Person)-[:CHAT]->(f:Message)<-[:CHAT]-(b:Person) , (f)-[:LAST_MESSAGE]->(l:Message), (l)<-[:NEXT*..10]-(m:Message) WHERE ID(a) = {id} AND ID(b) = {otherId} RETURN m.content AS content, m.at AS at, m.from AS from ORDER BY m.at',
			{'id': self._user_id, 'otherId': other_id})
		for message in result:
			if message['at'] != None and message['content'] != None:
				resList.append({'content': message['content'], 'at': message['at'], 'from': message['from']})
		return resList


	def storeMessageTo(self, to, message):
		GDSession().run('MATCH (a:Person)-[:CHAT]->(f:Message)<-[:CHAT]-(b:Person), (f)-[l:LAST_MESSAGE]->(c:Message) WHERE ID(a) = {id} AND ID(b) = {otherId} DELETE l CREATE (c)-[:NEXT]->(n:Message {at: {at}, content: {content}, from: {id}}), (f)-[:LAST_MESSAGE]->(n)',
			{'id': self._user_id, 'otherId': to, 'content': message, 'at': time.time()})

	def likeUser(self, otherId):
		result = GDSession().run('MATCH (a:Person), (b:Person) WHERE ID(b) = {otherId} AND ID(a) = {id} OPTIONAL MATCH (b)-[r:LIKED]->(a) MERGE (a)-[d:LIKED]->(b) RETURN r AS isMatch',
			{'id': self._user_id, 'otherId': otherId})
		for res in result:
			if res['isMatch'] != None:
				GDSession().run('MATCH (a:Person)-[l:LIKED]->(b:Person), (b)-[r:LIKED]->(a) WHERE ID(a) = {otherId} AND ID(b) = {id} SET r.match = true, l.match = true MERGE (a)-[:CHAT {with: {id}}]->(m:Message)<-[:CHAT {with: {otherId}}]-(b) MERGE (m)-[:LAST_MESSAGE]->(m)',
					{'id' : self._user_id, 'otherId' : otherId})
				return True
			else:
				return False
