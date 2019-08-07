from .models import Language, LanguageField
import re

def get_hosts():
	hosts = []

	for language in Language.objects.all():
		if language.host not in hosts:
			hosts.append(language.host)

	return hosts

def get_language(host, language):
	kwargs = {"host__iexact": host}

	if language is None:
		kwargs["default"] = True
	else:
		kwargs["code__iexact"] = language

	try:
		return Language.objects.get(**kwargs)
	except Language.DoesNotExist:
		return None

def get_languages(host):
	return Language.objects.filter(host__iexact=host)

def get_language_from_request(host, request):
	if "language" in request.session:
		language = get_language(host, request.session["language"])

		if language is not None:
			return language
	elif "HTTP_ACCEPT_LANGUAGE" in request.META:
		languages = get_languages(host)

		groups = re.findall(
			r"(?i)([a-z]{2})(?:-[a-z]{2})?",
			request.META["HTTP_ACCEPT_LANGUAGE"].lower()
		)
		length = len(groups)
		matches = {}
		default = None

		for language in groups:
			for _language in languages:
				if language == _language.code:
					return _language

				if _language.default:
					default = _language
		return default
	return get_language(host, None)

def get_fields(language, apply_default=True):
	fields, field_values = [], {}
	written_ids = {}

	if apply_default:
		try:
			default = Language.objects.get(host__iexact=language.host, default=True)
		except Language.DoesNotExist:
			default = None

		if default is not None:
			for field in LanguageField.objects.filter(host__iexact=language.host, language__iexact=default.code):
				written_ids[field.id] = field
				fields.append(field)
				if field.state == 3:
					field_values[field.field] = field.value

			if default.code == language.code:
				return fields, field_values

	for field in LanguageField.objects.filter(host__iexact=language.host, language__iexact=language.code):
		if field.id in written_ids:
			fields.remove(written_ids[field.id])
		fields.append(field)
		if field.state == 3:
			field_values[field.field] = field.value

	return fields, field_values