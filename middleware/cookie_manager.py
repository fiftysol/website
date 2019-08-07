class CookieManagerMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response

	def cookie_wrappers(self, request):
		request.COOKIE_WRAPPER_INSTRUCTIONS = []

		def set(*args, **kwargs):
			request.COOKIE_WRAPPER_INSTRUCTIONS.append(["set", args, kwargs])

		def rem(*args, **kwargs):
			request.COOKIE_WRAPPER_INSTRUCTIONS.append(["rem", args, kwargs])

		request.set_cookie = set
		request.delete_cookie = rem

	def __call__(self, request):
		self.cookie_wrappers(request)

		response = self.get_response(request)

		for instruction in request.COOKIE_WRAPPER_INSTRUCTIONS:
			function = response.set_cookie if instruction[0] == "set" else response.delete_cookie

			function(*instruction[1], **instruction[2])

		return response