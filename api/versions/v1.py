#coding: utf8

import django.middleware.csrf as csrf

from django.http import HttpRequest, HttpResponse, HttpResponseRedirect
from urllib.parse import urlencode
from common.utils import send_and_recv

import translation.backend as translation
import projects.backend as projects
import common.classes as classes
import api.versions.base as base
import datetime
import requests
import json
import os
import re

import matplotlib as mpl
mpl.use("Agg")
mpl.rcParams["xtick.color"] = "gray"
mpl.rcParams["ytick.color"] = "gray"
mpl.rcParams["text.color"] = "gray"
from matplotlib import pyplot as plt

def supported_methods(name, *methods):
	text = f"/{name}/ endpoint only supports " + (", ".join(methods[:-1]) if len(methods) > 1 else methods[0]) + " requests, but not "
	def decorator(fnc):
		def wrapper(self, request, *args, **kwargs):
			if request.method not in methods:
				return classes.ErrorJSONResponse(text + request.method + " ones.", status=405)
			return fnc(self, request, *args, **kwargs)
		return wrapper
	return decorator

def get_permissions(host, access, user_id, *accesses):
	role_ids = accesses[0]
	if host == "@website": # Website specific translations
		return (
			(access & 1) or
			(access & 2 and "494665355327832064" in role_ids) or
			(access & 8 and "585148219395276801" in role_ids) or
			(user_id == "285878295759814656")
		), (
			(access & 16 and "494665355327832064" in role_ids) or
			(access & 64 and "585148219395276801" in role_ids) or
			(user_id == "285878295759814656")
		)

	elif host[0] == ":": # Custom projects
		member = accesses[1]
		return (
			(access & 1) or
			(access & 2 and "494665355327832064" in role_ids) or
			(access & 4 and member is not None) or
			(access & 8 and "585148219395276801" in role_ids) or
			(member.owner)
		), (
			(access & 16 and "494665355327832064" in role_ids) or
			(access & 32 and member is not None) or
			(access & 64 and "585148219395276801" in role_ids) or
			(member.owner)
		)

	else: # Custom modules
		role_names = accesses[1]
		return (
			(access & 1) or
			(access & 2 and "494665355327832064" in role_ids) or
			(access & 4 and f"⚙ #{host}" in role_names) or
			(access & 8 and "585148219395276801" in role_ids) or
			(f"★ #{host}" in role_names)
		), (
			(access & 16 and "494665355327832064" in role_ids) or
			(access & 32 and f"⚙ #{host}" in role_names) or
			(access & 64 and "585148219395276801" in role_ids) or
			(f"★ #{host}" in role_names)
		)

def is_subset(a, b):
	if b & projects.ADMINISTRATOR:
		return False
	for bit in range(max(a.bit_length(), b.bit_length())):
		if (not a & (1 << bit)) and (b & (1 << bit)):
			return False
	return True

def is_superset(a, b):
	return is_subset(b, a)

class GraphsEndpoint:
	available_graphs = [
		"commands",
		"messages",
		"members/active",
		"members/active/explain",
		"members/flow"
	]
	graph_key_pairs = {
		"commands": ("b", ("bot", "global"), ("Bot Commands", "Global Commands", "Used Commands")),
		"messages": ("c", ("normal", "staff"), ("Normal Members", "Staff Members", "Sent Messages")),
		"members/flow": ("m", ("joined", "left"), ("Joined", "Left", "Members Flow"))
	}
	graphs_node = "https://discbotdb.000webhostapp.com/get?k=&f=b_serveractivity"

	def sort_graphs(self, date):
		return datetime.datetime.strptime(date, "%d/%m/%Y")

	def get_graphs_data(self, graph, *, parsed, limit):
		if graph not in self.available_graphs:
			return

		elif graph == "members/active/explain" and parsed:
			raise classes.DeepReturn(
				classes.ErrorJSONResponse(
					"Can't extract drawable data from this graph. Try with members/active instead.",
					status=400
				)
			)

		response = requests.get(self.graphs_node)

		if response.status_code == 200:
			response = response.json()

		else:
			raise classes.DeepReturn(
				classes.JSONResponse({
					"error": "Can't fetch the graphs data.",
					"info": "The graphs node answered in a non-proper way",
					"node_status_code": response.status_code,
					"node_response": response.text
				}, success=False, status=502)
			)

		dates = sorted(response.keys(), key=self.sort_graphs)[-limit:]
		result = {}

		if not parsed:
			if graph == "members/active":
				for date in dates:
					if "l" in response[date]:
						result[date] = len(response[date]["l"])

					else:
						result[date] = None

			elif graph == "members/active/explain":
				for date in dates:
					if "l" in response[date]:
						result[date] = response[date]["l"]

					else:
						result[date] = None

			else:
				pairs = self.graph_key_pairs[graph]

				for date in dates:
					if pairs[0] in response[date]:
						result[date] = { # It has a fixed for now length so it is faster to not make a calculation
							pairs[1][0]: response[date][pairs[0]][0],
							pairs[1][1]: response[date][pairs[0]][1]
						}

					else:
						result[date] = None

		else:
			result["data"] = []
			result["dates"] = dates
			result["title"] = None
			result["labeled"] = True

			if graph == "members/active":
				result["title"] = "Active members"
				result["labeled"] = False

				data = []
				to_remove = []
				for date in dates:
					if "l" in response[date]:
						data.append(len(response[date]["l"]))

					else:
						to_remove.append(date)

				for date in to_remove:
					result["dates"].remove(date)

				result["data"].append([data, None])

			else:
				pairs = self.graph_key_pairs[graph]
				result["title"] = pairs[2][2]

				data = [[], []]
				to_remove = []
				for date in dates:
					if pairs[0] in response[date]:
						data[0].append(response[date][pairs[0]][0])
						data[1].append(response[date][pairs[0]][1])

					else:
						to_remove.append(date)

				for date in to_remove:
					result["dates"].remove(date)

				result["data"].append([data[0], pairs[2][0]])
				result["data"].append([data[1], pairs[2][1]])

		return result

	@supported_methods("graphs", "GET")
	def graphs_view(self, request, path, *, action, graph=None):
		action = action.lower()
		if graph is not None:
			graph = graph.lower()

		if action == "available" and graph is None:
			return {"graphs": self.available_graphs}

		elif action == "data" and graph is not None:
			if graph in self.available_graphs:
				return self.get_graphs_data(
					graph,
					parsed=False,
					limit=int(request.GET["limit"]) if "limit" in request.GET else 30
				)

			else:
				return classes.ErrorJSONResponse("Can't get data from this graph", status=404)

		elif action == "draw" and graph is not None:
			if graph in self.available_graphs:
				result = self.get_graphs_data(
					graph,
					parsed=True,
					limit=int(request.GET["limit"]) if "limit" in request.GET else 30
				)

				for line in result["data"]:
					plt.plot(result["dates"], line[0], label=line[1])

				if result["labeled"]:
					plt.legend()

				plt.title(result["title"])
				plt.xticks(list(range(len(result["dates"]))), result["dates"], rotation="vertical", fontsize=8)
				plt.savefig("fig.png", transparent=True, bbox_inches="tight")
				plt.close()

				with open("fig.png", "rb") as file:
					response = HttpResponse(file.read(), content_type="image/png", status=200)
				return response

			else:
				return classes.ErrorJSONResponse("Graph not found.", status=404)

		else:
			return classes.ErrorJSONResponse("Malformed request", status=400)

class AnnouncementsEndpoint:
	@supported_methods("announcements", "GET")
	def announcements_view(self, request, path, *, channel="big", page="0"):
		page = int(page)
		if not (9 >= page >= 0):
			return classes.ErrorJSONResponse("Invalid page. Must be a page from 0 to 9.", status=400)

		data = send_and_recv(request.globals.socket, {
			"type": "fetch_announcements",
			"small": channel=="small",
			"page": page
		})
		return classes.JSONResponse({"messages": data["messages"]})

class OAuth2Endpoint:
	@supported_methods("oauth2", "GET")
	def oauth2_authorized_view(self, request, path):
		code = request.GET.get("code")
		state = request.GET.get("state")
		stored_link = request.session.get("oauth2_link")
		stored_state = request.session.get("oauth2_state")

		if (state is None) or (stored_link is None) or (stored_state is None) or (state != stored_state):
			return classes.ErrorJSONResponse("Missing parameters", status=400)

		del request.session["oauth2_link"]
		del request.session["oauth2_state"]

		if request.discord.logged:
			return classes.ErrorJSONResponse("You must log out first", status=400)

		if code is not None and not request.discord.login(code):
			return classes.ErrorJSONResponse("Invalid parameters", status=400)

		return HttpResponseRedirect(("/" if stored_link[0] != "/" else "") + stored_link)

	@supported_methods("oauth2", "GET")
	def oauth2_authorize_view(self, request, path):
		link = request.GET.get("link", "/")

		request.discord.logout()
		state = request.user.generate_state()

		request.session["oauth2_link"] = link
		request.session["oauth2_state"] = state
		request.session["welcomed"] = False

		link = "https://discordapp.com/api/oauth2/authorize?" + urlencode({
			"client_id": os.getenv("FSOL_OAUTH2_CLIENT_ID"),
			"redirect_uri": "http://" + request.globals.host + "/api/oauth2/authorized/",
			"response_type": "code",
			"scope": "identify",
			"state": state
		}).replace("+", "%20")
		return HttpResponseRedirect(link)

	@supported_methods("oauth2", "GET")
	def oauth2_logout_view(self, request, path):
		request.discord.logout()
		return HttpResponseRedirect("/")

class TranslationEndpoint:
	available_compile_outputs = ("json", "lua")

	def translation_sanitize(self, value, output):
		if output in ("json", "lua"):
			return value.replace("\r", "\\r").replace("\n", "\\n").replace("\t", "\\t").replace('"', '\\"')

	def translation_compile_to_json(self, queryset, language):
		compiled = '"' + self.translation_sanitize(language.code, "json") + '": {'
		length = len(queryset)
		pointer = 0

		compiled += '\n\t"host": "' + self.translation_sanitize(language.host, "json") + '",'
		compiled += '\n\t"name": "' + self.translation_sanitize(language.name, "json") + '"'
		if length > 0:
			compiled += ","

		for field in queryset:
			pointer += 1
			compiled += '\n\t"' + self.translation_sanitize(field.field, "json") + '": "' + self.translation_sanitize(field.value, "json") + '"'
			if pointer < length:
				compiled += ","

		return compiled + "\n}"

	def translation_compile_to_lua(self, queryset, language):
		valid_name = re.compile(r"^[A-Za-z_]\w*$")

		compiled = '["' + self.translation_sanitize(language.code, "lua") + '"] = {'

		compiled += '\n\thost = "' + self.translation_sanitize(language.host, "lua") + '",'
		compiled += '\n\tname = "' + self.translation_sanitize(language.name, "lua") + '",'
		for field in queryset:
			if valid_name.search(field.field) is not None:
				compiled += '\n\t' + field.field + ' = "' + self.translation_sanitize(field.value, "lua") + '",'
			else:
				compiled += '\n\t["' + self.translation_sanitize(field.field, "lua") + '"] = "' + self.translation_sanitize(field.value, "lua") + '",'

		return compiled + "\n}"

	@supported_methods("translate/{host}/{language}", "POST", "DELETE", "PATCH", "GET")
	def translation_view(self, request, path, *, host, language, fields=None):
		host = host.lower()
		language = language.lower()

		if request.method == "POST" and language != "auto" and fields is None: # Adding a new language
			if language == "xx":
				return classes.ErrorJSONResponse(f"The given language \"xx\" is not valid since it is a reserved keyword in a translation endpoint.", status=400)

			elif not request.user.logged:
				return classes.ErrorJSONResponse("You must be logged in first in order to add/modify a language.", status=403)

			if host[0] == ":": # It is a project!
				user = projects.get_project_user(host[1:], request.user.id)

				if user is None:
					return classes.ErrorJSONResponse("The project was not found or you're not a project member.", status=403)
				elif (not user.permissions & project.CREATE_LANGUAGE) and (not user.permissions & project.ADMINISTRATOR) and not user.owner:
					return classes.ErrorJSONResponse("You need the CREATE_LANGUAGE permission in order to do it.", status=403)

			else:
				data = send_and_recv(request.globals.socket, {
					"type": "user_roles",
					"user": request.user.id
				})
				if host == "@website":
					if not "585148219395276801" in data["role_ids"] and request.user.id != "285878295759814656":
						return classes.ErrorJSONResponse(
							"You need the moderator role in the discord server in order to add/modify a language owned by @website.", status=403
						)

				elif not f"★ #{host}" in data["role_names"]:
					return classes.ErrorJSONResponse(
						f"You need to be #{host} owner in the discord server in order to add/modify a language owned by the module.", status=403
					)

			code = language
			language = translation.get_language(host, language)
			if language is None:
				if not ("default" in request.data and "name" in request.data and "access" in request.data):
					return classes.ErrorJSONResponse("Adding a new language requires default, name and access parameters.", status=400)

				else:
					language = translation.Language.objects.create(
						host=host, default=request.data["default"],
						code=code, name=request.data["name"], access=request.data["access"]
					)

			else:
				for parameter in ["host", "default", "name", "access"]:
					if parameter in request.data:
						setattr(language, parameter, request.data[parameter])

			language.save()

		elif request.method == "DELETE" and language != "auto" and fields is None: # Deleting a language
			if not request.user.logged:
				return classes.ErrorJSONResponse("You must be logged in first in order to add/modify a language.", status=403)

			if host[0] == ":":
				user = projects.get_project_user(host[1:], request.user.id)

				if user is None:
					return classes.ErrorJSONResponse("The project was not found or you're not a project member.", status=403)
				elif (not user.permissions & project.ADMINISTRATOR) and not user.owner:
					return classes.ErrorJSONResponse("You need the ADMINISTRATOR permission in order to do it.", status=403)

			else:
				data = send_and_recv(request.globals.socket, {
					"type": "user_roles",
					"user": request.user.id
				})
				if host == "@website":
					if not "585148219395276801" in data["role_ids"] and request.user.id != "285878295759814656":
						return classes.ErrorJSONResponse(
							"You need the moderator role in the discord server in order to delete a language owned by @website.", status=403
						)

				elif not f"★ #{host}" in data["role_names"]:
					return classes.ErrorJSONResponse(
						f"You need to be #{host} owner in the discord server in order to delete a language owned by the module.", status=403
					)

			language = translation.get_language(host, language)
			if language is None:
				return classes.ErrorJSONResponse("The given host-language pair was not found.", status=404)

			language.delete()

		elif request.method == "PATCH" and language != "auto" and fields is None: # Updating a field
			if not request.user.logged:
				return classes.ErrorJSONResponse("You must be logged in first in order to add/modify a language.", status=403)

			language = translation.get_language(host, language)
			if language is None:
				return classes.ErrorJSONResponse("The given host-language pair was not found.", status=404)

			data = send_and_recv(request.globals.socket, {
				"type": "user_roles",
				"user": request.user.id
			})
			if host[0] == ":":
				user = projects.get_project_user(host[1:], request.user.id)

				create, edit = get_permissions(language.host, language.access, request.user.id, data["role_ids"], user is not None)
			else:
				create, edit = get_permissions(language.host, language.access, request.user.id, data["role_ids"], data["role_names"])

			if not create and not edit:
				return classes.ErrorJSONResponse("You can't edit or create any translation field in the given host-language pair.", status=403)

			if "fields" in request.data:
				update_bulk = [[], [], [], []]
				create_bulk = []

				for field in request.data["fields"]:
					if "id" in field and "state" in field and field["state"] != 0 and field["state"] != "0":
						if not edit:
							return classes.ErrorJSONResponse("You can't edit the state of a translation field in the given host-language pair.", status=403)

						field["state"] = int(field["state"])
						update = True
						update_bulk[field["state"]].append(field["id"])

					elif "field" in field and "value" in field:
						if not create:
							return classes.ErrorJSONResponse("You can't create a translation field in the given host-language pair.", status=403)
						elif "/" in field["field"]:
							return classes.ErrorJSONResponse(f"The fields can not have / in them, but \"{field['field']}\" does.", status=400)
						elif field["field"] == "verbose" or field["field"] == "all":
							return classes.ErrorJSONResponse(
								f"The given field \"{field['field']}\" is not valid since it is a reserved keyword in a translation endpoint.", status=400
							)

						create = True
						create_bulk.append(translation.LanguageField(
							state=0, owner_id=request.user.id, state_id=0,
							host=host, language=language.code,
							field=field["field"], value=field["value"]
						))

					else:
						return classes.ErrorJSONResponse("Malformed request.", status=400)

				for state, bulk in enumerate(update_bulk):
					if len(bulk) > 0:
						translation.LanguageField.objects.filter(host__iexact=host, id__in=bulk).update(state_id=request.user.id, state=state)

				if len(create_bulk) > 0:
					translation.LanguageField.objects.bulk_create(create_bulk)
			else:
				return classes.ErrorJSONResponse("Malformed request.", status=400)

		elif request.method == "GET": # Getting fields
			verbose = False

			if fields is None:
				fields = "all"
			else:
				_fields = fields.lower().split("/")
				if _fields[0] == "verbose":
					_fields.pop(0)
					verbose = True

				while "" in _fields:
					_fields.remove("")

				if _fields == ["all"] or _fields == []:
					fields = "all"
				else:
					fields = []
					for item in _fields:
						if item in fields:
							continue
						fields.append(item)

			if language == "auto":
				language = translation.get_language_from_request(host, request)
				if language is None:
					language = translation.get_language(host, None)
			else:
				language = translation.get_language(host, language)

			if language is None:
				return classes.ErrorJSONResponse("The given host-language pair was not found.", status=404)

			if host[0] == ":":
				if request.user.logged:
					data = send_and_recv(request.globals.socket, {
						"type": "user_roles",
						"user": request.user.id
					})
					user = projects.get_project_user(host[1:], request.user.id)

					create, edit = get_permissions(language.host, language.access, request.user.id, data["role_ids"], user is not None)
				else:
					create, edit = get_permissions(language.host, language.access, "0", [], False)

				if not create:
					return classes.ErrorJSONResponse("Missing permissions.", status=403)

			else:
				if language.access & 1:
					pass
				elif request.user.logged:
					data = send_and_recv(request.globals.socket, {
						"type": "user_roles",
						"user": request.user.id
					})
					if not create:
						return classes.ErrorJSONResponse("Missing permissions.", status=403)
				else:
					return classes.ErrorJSONResponse("Missing permissions.", status=403)

			response = {
				"default": language.default,
				"access": language.access,
				"code": language.code,
				"name": language.name,
				"host": language.host,
				"fields": [] if verbose else {}
			}

			language_fields = translation.get_fields(language)

			if not verbose:
				language_fields = language_fields[1]
				if fields == "all":
					response["fields"] = language_fields

				else:
					default = "default" not in request.GET

					for field in fields:
						response["fields"][field] = language_fields[field] if field in language_fields else (f"%{field}%" if default else None)

			else:
				language_fields = language_fields[0]
				_request = []

				for field in language_fields:
					if fields == "all" or field.field in fields or str(field.id) in fields:
						_request.append(field.owner_id)
						if field.state_id != 0:
							_request.append(field.state_id)

				data = send_and_recv(request.globals.socket, {
					"type": "get_user_info",
					"users": _request
				})
				user_names = {}
				for user, data in data.items():
					if user.isdigit():
						user_names[int(user)] = data["name"] if data is not None else None

				for field in language_fields:
					id = str(field.id)
					if fields == "all" or field.field in fields or id in fields:
						response["fields"].append({
							"id": id,
							"state": field.state,
							"language": field.language,
							"owner_id": str(field.owner_id),
							"owner_name": user_names[field.owner_id],
							"state_id": str(field.state_id) if field.state_id != 0 else None,
							"state_name": user_names[field.state_id] if field.state_id != 0 else None,
							"field": field.field,
							"value": field.value
						})

			return classes.JSONResponse(response)

		else:
			return classes.ErrorJSONResponse("Malformed request.", status=400)

	@supported_methods("translate/compile", "PUT", "GET")
	def translation_compile_view(self, request, path, *, host, language):
		host = host.lower()
		language = language.lower()

		if request.method == "PUT":
			if not request.user.logged:
				return classes.ErrorJSONResponse("You must be logged in first in order to add/modify a language.", status=403)

			language = translation.get_language(host, language)
			if language is None:
				return classes.ErrorJSONResponse("The given host-language pair was not found.", status=404)

			data = send_and_recv(request.globals.socket, {
				"type": "user_roles",
				"user": request.user.id
			})
			if host[0] == ":":
				user = projects.get_project_user(host[1:], request.user.id)

				create, edit = get_permissions(language.host, language.access, request.user.id, data["role_ids"], user is not None)
			else:
				create, edit = get_permissions(language.host, language.access, request.user.id, data["role_ids"], data["role_names"])

			if not (create and edit):
				return classes.ErrorJSONResponse("You must be able to create and edit translation fields in the given host-language pair.")

			bulk = []
			if isinstance(request.data, dict):
				for key, value in request.data.items():
					if not isinstance(value, str):
						return classes.ErrorJSONResponse("The values must be strings. You can't have nested arrays or other type of values.", status=400)
					elif "/" in key:
						return classes.ErrorJSONResponse(f"The fields can not have / in them, but \"{key}\" does.", status=400)
					elif key == "verbose" or key == "all":
						return classes.ErrorJSONResponse(
							f"The given field \"{key}\" is not valid since it is a reserved keyword in a translation endpoint.",
							status=400
						)
					bulk.append(translation.LanguageField(
						state=3, owner_id=request.user.id, state_id=request.user.id,
						host=language.host, language=language.code,
						field=key, value=value
					))
			else:
				return classes.ErrorJSONResponse("Malformed request.", status=400)

			queryset = translation.LanguageField.objects.filter(host__iexact=language.host, language__iexact=language.code, state=3)
			queryset.update(state_id=request.user.id, state=2)
			translation.LanguageField.objects.bulk_create(bulk)

		elif request.method == "GET":
			if "output" not in request.GET:
				return classes.ErrorJSONResponse("You must specify an output GET parameter to know what to generate.", status=400)
			elif request.GET["output"].lower() not in self.available_compile_outputs:
				return classes.ErrorJSONResponse(f"The given output is not available. Available ones: {', '.join(self.available_compile_outputs)}", status=400)
			else:
				output = request.GET["output"].lower()

			if language == "xx":
				languages = translation.get_languages(host)
				if request.user.logged:
					data = send_and_recv(request.globals.socket, {
						"type": "user_roles",
						"user": request.user.id
					})
					user = projects.get_project_user(host[1:], request.user.id)

				for language in languages:
					if host[0] == ":":
						create, edit = get_permissions(
							language.host, language.access, request.user.id if request.user.logged else "0",
							data["role_ids"] if request.user.logged else [], user is not None if request.user.logged else False
						)

						if not create:
							return classes.ErrorJSONResponse("Missing permissions.", status=403)
					else:
						if language.access & 1:
							continue
						elif request.user.logged:
							create, edit = get_permissions(language.host, language.access, request.user.id, data["role_ids"], data["role_names"])
							if not create:
								return classes.ErrorJSONResponse("Missing permissions.", status=403)
						else:
							return classes.ErrorJSONResponse("Missing permissions.", status=403)

				fnc = getattr(self, f"translation_compile_to_{output}")
				result = []
				for language in languages:
					queryset = translation.LanguageField.objects.filter(host__iexact=language.host, language__iexact=language.code, state=3)
					result.append(fnc(queryset, language))
				return HttpResponse(",\n".join(result), content_type="text/plain")

			language = translation.get_language(host, language)
			if language is None:
				return classes.ErrorJSONResponse("The given host-language pair was not found.", status=404)

			if host[0] == ":":
				if request.user.logged:
					data = send_and_recv(request.globals.socket, {
						"type": "user_roles",
						"user": request.user.id
					})
					user = projects.get_project_user(host[1:], request.user.id)

					create, edit = get_permissions(language.host, language.access, request.user.id, data["role_ids"], user is not None)
				else:
					create, edit = get_permissions(language.host, language.access, "0", [], False)

				if not create:
					return classes.ErrorJSONResponse("Missing permissions.", status=403)

			else:
				if language.access & 1:
					pass
				elif request.user.logged:
					data = send_and_recv(request.globals.socket, {
						"type": "user_roles",
						"user": request.user.id
					})
					if not create:
						return classes.ErrorJSONResponse("Missing permissions.", status=403)
				else:
					return classes.ErrorJSONResponse("Missing permissions.", status=403)

			queryset = translation.LanguageField.objects.filter(host__iexact=language.host, language__iexact=language.code, state=3)
			return HttpResponse(getattr(self, f"translation_compile_to_{output}")(queryset, language), content_type="text/plain")

	@supported_methods("translate/{host}", "GET")
	def translation_list(self, request, path, *, host):
		result = {}
		languages = translation.get_languages(host)
		for language in languages:
			result[language.code] = language.name

		return classes.JSONResponse({"host": host, "list": result})

	@supported_methods("translate", "GET", "PUT")
	def translation_language_selector(self, request, path):
		if request.method == "GET":
			if "language" in request.session:
				return classes.JSONResponse({"language": request.session["language"]})

			else:
				return classes.ErrorJSONResponse("No language selected.", status=400)

		elif request.method == "PUT" and "language" in request.data and len(request.data["language"]) == 2:
			request.session["language"] = request.data["language"].lower()

		else:
			return classes.ErrorJSONResponse("Malformed request.", status=400)

class ProjectsEndpoint:
	def get_project_dict(self, request, project):
		project = projects.get_project(project)

		if project is None:
			return None

		elif (not request.user.logged) and (not project.public):
			return None

		users = []
		result = {
			"name": project.name,
			"description": project.description,
			"public": project.public,
			"owner": None,
			"im_in": False,
			"users": users
		}
		available = project.public
		if not project.public:
			me = int(request.user.id)

		_users = projects.get_project_users(project)
		not_public_users = []
		for user in _users:
			if request.user.logged and user.id == me:
				result["im_in"] = True
				available = True

			user_result = {
				"id": user.id,
				"role": user.role,
				"owner": user.owner,
				"public": user.public,
				"permissions": user.permissions
			}
			if not user.public:
				not_public_users.append(user_result)
			else:
				if user.owner:
					result["owner"] = user_result
				users.append(user_result)

		if result["im_in"]:
			result["users"].extend(not_public_users)

		if available:
			return result
		return None

	@supported_methods("projects/members", "POST", "PATCH", "DELETE")
	def projects_members_view(self, request, path, *, filter):
		filter = filter.lower()

		if "users" not in request.data or not isinstance(request.data["users"], list):
			return self.malformed()

		if request.method == "POST": # Add a new member
			for user in request.data["users"]:
				if not isinstance(user, str) or not user.isdigit():
					return self.malformed()

			if not request.user.logged:
				return ErrorJSONResponse("You must be logged in first in order to do this.", status=403)

			user = projects.get_project_user(filter, request.user.id)
			if user is None:
				return ErrorJSONResponse("The project was not found or you're not a member of it.", status=404)

			elif (not user.permissions & projects.ADD_NEW_MEMBERS) and (not user.permissions & projects.ADMINISTRATOR) and not user.owner:
				return ErrorJSONResponse("You need the ADD_NEW_MEMBERS permission in order to do this.", status=403)

			data = send_and_recv({
				"type": "get_user_info",
				"users": request.data["users"]
			})
			bulk = []
			result = {}
			for user in request.data["users"]:
				if data[user] is not None:
					bulk.append(projects.ProjectUser(
						id=user, role="Member", project=user.project,
						owner=False, public=False, permissions=0
					))
					result[user] = True
				else:
					result[user] = False

			if len(bulk) > 0:
				projects.ProjectUser.objects.bulk_create(bulk)
			return JSONResponse(result)

		elif request.method == "PATCH": # Edit a member
			user_ids = {}
			for user in request.data["users"]:
				if not isinstance(user, dict) or "id" not in user or not isinstance(user["id"], str) or not user["id"].isdigit():
					return self.malformed()
				else:
					user_ids[int(user["id"])] = user

			if not request.user.logged:
				return ErrorJSONResponse("You must be logged in first in order to do this.", status=403)

			me = None
			users = projects.get_project_users(filter)
			if users is None:
				return ErrorJSONResponse("The project was not found.", status=404)
			for user in users:
				if str(user.id) == request.user.id:
					me = user
					break
			if me is None:
				return ErrorJSONResponse("You're not a member of the project.", status=404)

			elif (not me.permissions & projects.EDIT_PERMISSIONS) and (not me.permissions & projects.ADMINISTRATOR) and not me.owner:
				return ErrorJSONResponse("You need the EDIT_PERMISSIONS permission in order to do this.", status=403)

			if not me.owner:
				for user in users:
					if user.id in user_ids:
						if not (user.permissions != me.permissions and is_subset(me.permissions, user.permissions)) and user.id != me.id:
							return ErrorJSONResponse(f"You can't edit <@{user.id}>'s data.", status=403)

			for user in users:
				if user.id in user_ids:
					_user = user_ids[user.id]
					if me.owner or user.id != me.id:
						if "role" in _user:
							user.role = _user["role"]
						if me.owner and "public" in _user:
							user.public = _user["public"]
						if "permissions" in _user:
							if is_subset(me.permissions, _user["permissions"]) or me.owner:
								user.permissions = _user["permissions"]

					elif user.id == me.id:
						if "public" in _user:
							user.public = _user["public"]

		elif request.method == "DELETE": # Remove a member
			for user in request.data["users"]:
				if not isinstance(user, str) or not user.isdigit():
					return self.malformed()

			if not request.user.logged:
				return ErrorJSONResponse("You must be logged in first in order to do this.", status=403)

			if request.data["users"] == [request.user.id]:
				user = projects.get_project_user(filter, request.user.id)
				if user is None:
					return ErrorJSONResponse("The project was not found or you're not a project member.", status=404)
				if user.owner:
					return ErrorJSONResponse("You can't leave the project. Delete it instead.", status=403)
				else:
					user.delete()
				return

			me = None
			users = projects.get_project_users(filter)
			if users is None:
				return ErrorJSONResponse("The project was not found.", status=404)
			for user in users:
				if str(user.id) == request.user.id:
					me = user
					break
			if me is None:
				return ErrorJSONResponse("You're not a member of the project.", status=403)

			elif (not me.permissions & projects.REMOVE_MEMBERS) and (not me.permissions & projects.ADMINISTRATOR) and not me.owner:
				return ErrorJSONResponse("You need the REMOVE_MEMBERS permission in order to do this.", status=403)

			if not me.owner:
				for user in users:
					if str(user.id) in request.data["users"]:
						if not (user.permissions != me.permissions and is_subset(me.permissions, user.permissions)):
							return ErrorJSONResponse(f"You can't remove <@{user.id}> from the project.", status=403)

			projects.ProjectUser.objects.filter(project__iexact=me.project, user__in=request.data["users"]).delete()

	@supported_methods("projects", "GET", "POST", "PATCH", "DELETE")
	def projects_view(self, request, path, *, filter_type, filter):
		filter = filter.lower()

		if (filter_type == "@") and ((not request.user.logged) or (filter != "me" and filter != "mine")):
			if filter.isdigit():
				filter = int(filter)
			else:
				return self.malformed()

		if request.method == "GET": # Get info about the project
			if filter_type == "@":
				result = {"projects": []}

				projects = projects.get_projects_by_user(filter, owner=filter == "mine")
				for project in projects:
					project = self.get_project_dict(request, project)

					if project is not None:
						result["projects"].append(project)

				return classes.JSONResponse(result)

			else:
				project = projects.get_project(filter)

				if project is not None:
					project = self.get_project_dict(request, project)

					if project is not None:
						return classes.JSONResponse(project)

					else:
						return classes.ErrorJSONResponse("The project is not public and you can't see it.", status=404)

				else:
					return classes.ErrorJSONResponse("Project not found", status=404)

		elif request.method == "POST": # Create a project
			if filter_type == "@":
				return self.malformed()

			if not request.user.logged:
				return classes.ErrorJSONResponse("You must be logged in first.", status=403)
			data = send_and_recv({
				"type": "user_roles",
				"user": request.user.id
			})
			if "Developer" not in data["role_names"]:
				return classes.ErrorJSONResponse("You must have the Developer role in the discord server first.", status=403)

			project = self.get_project(filter)
			if project:
				return classes.ErrorJSONResponse("The project already exists.", status=403)

			projects.Project.objects.create(
				name=filter,
				description=request.data["description"] if "description" in request.data else "",
				public=request.data["public"] if "public" in request.data else False
			).save()
			projects.ProjectUser.objects.create(
				id=request.user.id, role="Owner", project=filter,
				owner=True, public=True, permissions=1
			).save()

		elif request.method == "PATCH": # Update a project's information
			if filter_type == "@":
				return self.malformed()

			if not request.user.logged:
				return classes.ErrorJSONResponse("You must be logged in first.", status=403)

			user = projects.get_project_user(filter, request.user.id)
			if user is None:
				return classes.ErrorJSONResponse("The project does not exist or you're not a member.", status=403)

			if not (user.owner or user.permissions & projects.ADMINISTRATOR):
				if "description" in request.data and not user.permissions & projects.EDIT_DESCRIPTION:
					return classes.ErrorJSONResponse("You don't have the EDIT_DESCRIPTION permission.", status=403)
				elif "name" in request.data and not user.permissions & projects.EDIT_NAME:
					return classes.ErrorJSONResponse("You don't have the EDIT_NAME permission.", status=403)
				elif "public" in request.data and not user.permissions & projects.EDIT_PUB_STATE:
					return classes.ErrorJSONResponse("You don't have the EDIT_PUB_STATE permission.", status=403)

			kwargs = {}
			if "description" in request.data:
				kwargs["description"] = request.data["description"]
			elif "name" in request.data:
				kwargs["name"] = request.data["name"].lower()
				translation.Language.objects.filter(host__iexact=filter).update(host=":" + kwargs["name"])
				translation.LanguageField.objects.filter(host__iexact=filter).update(host=":" + kwargs["name"])
				projects.ProjectUser.objects.filter(project__iexact=filter).update(project=kwargs["name"])
			elif "public" in request.data:
				kwargs["public"] = request.data["public"]

			projects.Project.objects.filter(name=filter).update(**kwargs)

		elif request.method == "DELETE": # Delete the project
			if filter_type == "@":
				return self.malformed()

			if not request.user.logged:
				return classes.ErrorJSONResponse("You must be logged in first.", status=403)

			user = projects.get_project_user(filter, request.user.id)
			if user is None:
				return classes.ErrorJSONResponse("The project does not exist or you're not a member.", status=403)

			if not user.owner:
				return classes.ErrorJSONResponse("You must be the project owner in order to delete it.", status=403)
			translation.Language.objects.filter(host__iexact=filter).delete()
			translation.LanguageFields.objects.filter(host__iexact=filter).delete()
			projects.ProjectUser.objects.filter(project__iexact=filter).delete()
			projects.Project.objects.filter(name__iexact=filter).delete()

class API(
		base.BaseAPIClass,
		GraphsEndpoint,
		AnnouncementsEndpoint,
		OAuth2Endpoint,
		TranslationEndpoint,
		ProjectsEndpoint
	):

	routes = {
		r"(?i)^graphs/+(?P<action>[^/]+)/+(?P<graph>.+?)/*$": "graphs_view",
		r"(?i)^graphs/+(?P<action>[^/]+)/*$": "graphs_view",
		r"(?i)^graphs/+.*$": "malformed",
		r"(?i)^graphs/*$": "malformed",

		r"(?i)^announcements/+(?P<channel>small|big)/+(?P<page>\d+)/*$": "announcements_view",
		r"(?i)^announcements/+(?P<channel>small|big)/*$": "announcements_view",
		r"(?i)^announcements/+(?P<page>\d+)/*$": "announcements_view",
		r"(?i)^announcements/*$": "announcements_view",
		r"(?i)^announcements/+.+$": "malformed",

		r"(?i)^oauth2/+authorized/*$": "oauth2_authorized_view",
		r"(?i)^oauth2/+authorize/*$": "oauth2_authorize_view",
		r"(?i)^oauth2/+logout/*$": "oauth2_logout_view",
		r"(?i)^oauth2/+.*$": "malformed",
		r"(?i)^oauth2/*$": "malformed",

		r"(?i)^translate/+compile/+(?P<host>[^/]+)/+(?P<language>.{2})/*$": "translation_compile_view",
		r"(?i)^translate/+(?P<host>[^/]+)/+(?P<language>auto|.{2})/+(?P<fields>.+)$": "translation_view",
		r"(?i)^translate/+(?P<host>[^/]+)/+(?P<language>auto|.{2})/*$": "translation_view",
		r"(?i)^translate/+(?P<host>[^/]+)/*$": "translation_list",
		r"(?i)^translate/*$": "translation_language_selector",
		r"(?i)^translate/+.*$": "malformed",

		r"(?i)^projects/+members/+:(?P<filter>[^/]+)/*$": "projects_members_view",
		r"(?i)^projects/+(?P<filter_type>:|@)(?P<filter>[^/]+)/*$": "projects_view",
		r"(?i)^projects/+.*": "malformed",
		r"(?i)^projects/*$": "malformed",
	}