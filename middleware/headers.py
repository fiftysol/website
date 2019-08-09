import re

class HeadersMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		if re.search(r"(?i)^api/", request.path) is not None:
			sessid = request.headers.get("session", None)
			if sessid is not None:
				request.COOKIES["sessionid"] = sessid

		response = self.get_response(request)
		response["server"] = "unknown"
		return response