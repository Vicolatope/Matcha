from neo4j.v1 import GraphDatabase, basic_auth

class GDSession():

	def __init__(self):
		self.driver = GraphDatabase.driver('bolt://localhost:7687', auth=basic_auth('neo4j', 'Homeland1'))
		self.session = self.driver.session()

	def close(self):
		self.session.close()

	def run(self, req, data=None):
		res = self.session.run(req, data)
		self.close()
		return res