from django.http import HttpResponse
import json

JSON_ITEM_ACCESSES = (
	"discord", "user", "globals", "session",
	"COOKIES", "method", "META"
)

class DeepReturn(Exception):
	"""This exception is raised when you need to make a deep return (you're in a low-level function, by example)."""
	def as_return(self):
		length = len(self.args)

		if length == 0:
			return None

		elif length == 1:
			return self.args[0]

		else:
			return self.args

class JSONResponse(HttpResponse):
	def __init__(self, data={}, success=True, status=200):
		data["success"] = success

		super().__init__(json.dumps(data), status=status, content_type="application/json")

class ErrorJSONResponse(JSONResponse):
	def __init__(self, message, status=200):
		super().__init__({"error": message}, success=False, status=status)

class JSONRequest:
	def __init__(self, request):
		self.request = request

	def load(self):
		for item in JSON_ITEM_ACCESSES:
			setattr(self, item, getattr(self.request, item, None))

		if self.method == "GET":
			self.GET = self.request.GET

		elif self.method == "POST":
			self.POST = self.request.POST

		try:
			if self.request.body == b"":
				self.data = {}

			else:
				self.data = json.loads(self.request.body)

		except:
			return ErrorJSONResponse("Malformed request.", status=400)

		return self