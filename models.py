
class User:
	""" Holder for the user object used by flask-login """

	def __init__(self, id=u'1'):
		self.id = id
		

	def is_authenticated(self):
		return True

	def is_active(self):
		return True

	def is_anonymous(self):
		return False

	def get_id(self):
		return self.id

	@classmethod
	def get(random_variable, id):
		return User()