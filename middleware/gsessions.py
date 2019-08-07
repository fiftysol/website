class Globals:
	host = "181.230.170.155:5000"

	def __getattr__(self, name):
		return None

class GlobalSessionsMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response
		self.globals = Globals()

	def __call__(self, request):
		request.globals = self.globals

		return self.get_response(request)