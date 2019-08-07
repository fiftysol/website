from django.http import HttpResponse

import common.classes as classes
import api.versions as versions

default_api = None

for version, data in versions.index.items():
	if data[1] == "default":
		default_api = version
		break

def view(request, version, path):
	result = classes.JSONRequest(request).load()

	if isinstance(result, HttpResponse):
		return result
	if version not in versions.index:
		return classes.ErrorJSONResponse("The given API version was not found.", status=404)
	if versions.index[version][1] not in ["default", "stable"]:
		return classes.ErrorJSONResponse("The given API version can not be used.", status=400)

	result = versions.index[version][0](result, path)

	if isinstance(result, HttpResponse):
		return result
	if isinstance(result, tuple):
		return classes.JSONResponse(*result)
	return classes.JSONResponse(result)

def default_view(request, path):
	return view(request, default_api, path)