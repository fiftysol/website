import common.classes as classes
import traceback
import re

class BaseAPIClass:
	routes = {}

	def __init__(self):
		routes = {}

		for route, view in self.routes.items():
			routes[route] = getattr(self, view)

		self.routes = routes

	def malformed(self, *args, **kwargs):
		return classes.ErrorJSONResponse("Malformed request.", status=400)

	def view(self, request, path):
		for route, view in self.routes.items():
			match = re.search(route, path)

			if match is not None:
				try:
					response = view(request, path, **match.groupdict())

				except classes.DeepReturn as returned:
					response = returned.as_return()

				except:
					traceback.print_exc()
					return classes.ErrorJSONResponse("Internal server error.", status=500)

				if response is None:
					return classes.JSONResponse()
				return response
		return classes.ErrorJSONResponse("Route not found.", status=404)