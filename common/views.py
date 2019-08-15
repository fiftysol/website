from django.http import HttpResponse
from django.conf import settings
from django.urls import re_path

from django.shortcuts import render
from .classes import DeepReturn
from .utils import send_and_recv

import translation.backend as translation
import time
import os
import re

def as_color(color):
	h = hex(color)[2:]
	return "0" * (6 - len(h)) + h

def dropdown_menu_items(request, context):
	has = {"Module Member": False, "Developer": False, "Translator": False}
	is_member = False
	has_any_role = False
	if request.user.logged:
		try:
			data = send_and_recv(request.globals.socket, {
				"type": "user_roles",
				"user": request.user.id
			}, json=False)
		except DeepReturn:
			context["in_server"] = False
		else:
			if data["in_server"]:
				is_member = True
				context["in_server"] = True
				context["user_role_ids"] = data["role_ids"]
				context["user_roles"] = list(map(lambda role: (role[0], as_color(role[1])), data["role_colors"]))
				context["user_color"] = data["color"]
			else:
				context["in_server"] = False
			for role in has:
				if role in data["role_names"]:
					has_any_role = True
					has[role] = True

	return (
		{
			"show": is_member,
			"type": "header",
			"text": context["translate"]["member"].upper()
		},
		{
			"show": is_member,
			"type": "link",
			"link": "/members/@me/",
			"text": context["translate"]["my_profile"]
		},
		{
			"show": has["Module Member"],
			"type": "separator"
		},
		{
			"show": has["Module Member"],
			"type": "header",
			"link": "#",
			"text": context["translate"]["module_member"].upper()
		},
		{
			"show": has["Module Member"],
			"type": "link",
			"link": "#",
			"text": context["translate"]["my_commands"]
		},
		{
			"show": has["Module Member"],
			"type": "link",
			"link": "#",
			"text": context["translate"]["my_modules"]
		},
		{
			"show": has["Developer"],
			"type": "separator"
		},
		{
			"show": has["Developer"],
			"type": "header",
			"text": context["translate"]["developer"].upper()
		},
		{
			"show": has["Developer"],
			"type": "link",
			"link": "#",
			"text": context["translate"]["my_projects"]
		},
		{
			"show": has["Developer"],
			"type": "link",
			"link": "#",
			"text": context["translate"]["new_project"]
		},
		{
			"show": has["Translator"],
			"type": "separator"
		},
		{
			"show": has["Translator"],
			"type": "header",
			"text": context["translate"]["translator"].upper()
		},
		{
			"show": has["Translator"],
			"type": "link",
			"link": "#",
			"text": context["translate"]["translation_panel"]
		},
		{
			"show": is_member or has_any_role,
			"type": "separator"
		},
		{
			"show": True,
			"type": "link",
			"link": "/api/oauth2/logout",
			"text": context["translate"]["logout"]
		},
	)

class Static:
	content_types = {
		"css": "text/css",
		"csv": "text/csv",
		"html": "text/html",

		"mp4": "video/mp4",

		"gif": "image/gif",
		"png": "image/png",
		"jpg": "image/jpeg",
		"jpeg": "image/jpeg",
		"webp": "image/webp",

		"js": "application/javascript",
		"ogg": "application/ogg",
		"zip": "application/zip",
		"pdf": "application/pdf",
		"xml": "application/xml",
		"json": "application/json"
	}

	def get_file(self, dir, file):
		with open(os.path.join(dir, file), "rb") as obj:
			file = os.path.basename(file)
			content_type = "text/plain"

			if "." in file:
				extension = file.split(".")[-1].lower()

				if extension in self.content_types:
					content_type = self.content_types[extension]

			return HttpResponse(obj.read(), content_type=content_type)

	def view(self, request, *, path):
		path = path.replace("\\", "/")
		if path == ".." or path.startswith("../") or "/../" in path:
			return HttpResponse("404 Not Found", content_type="text/plain", status=404)

		try:
			return self.get_file(settings.STATIC_ROOT, path)
		except FileNotFoundError:
			return HttpResponse("404 Not Found", content_type="text/plain", status=404)
		except:
			return HttpResponse("500 Server Error", content_type="text/plain", status=500)

class TranslationDictWrapper:
	def __init__(self, data):
		self.data = data

	def __getitem__(self, key):
		return self.data.get(key, f"%{key}%")

class TemplateRenderer:
	template = None
	regex = ""
	args = []
	kwargs = {}
	context = {}
	content_type = None
	status = None
	using = None
	dont_translate = False

	def as_url(self):
		if self.template is None:
			raise NotImplementedError("TemplateRenderer.as_url requires TemplateRenderer.template not to be None.")

		return re_path(self.regex, self.view, *self.args, **self.kwargs)

	def before(self, request, context):
		return request, context

	def after(self, request, rendered, context):
		return rendered

	def view(self, request, **kwargs):
		context = self.context.copy()

		context["request"] = request
		for key, value in kwargs.items():
			context[key] = value

		context["welcome_user"] = False
		context["right_now"] = time.time()

		if request.user.logged:
			if "welcomed" not in request.session or not request.session["welcomed"]:
				request.session["welcomed"] = True
				context["welcome_user"] = True

		if not self.dont_translate:
			translate = translation.get_fields(translation.get_language_from_request("@website", request), apply_default=True)
			context["translate_v"] = TranslationDictWrapper(translate[0])
			context["translate"] = TranslationDictWrapper(translate[1])

		request, context = self.before(request, context)
		if not "dropdown_menu_items" in context:
			context["dropdown_menu_items"] = dropdown_menu_items(request, context)
		rendered = render(request, self.template, context=context, content_type=self.content_type, status=self.status, using=self.using)
		return self.after(request, rendered, context)

class DynamicTemplate(TemplateRenderer):
	template = "dynamic.html"
	regex = r".*"