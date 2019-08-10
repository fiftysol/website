from . import models
from . import backend

try:
	if backend.get_language("@website", "en") is None:
		print("Language @website/en does not exist. Creating it...")
		models.Language(host="@website", default=True, code="en", name="English", access=75).save()
		print("Language @website/en was created.")
except:
	print("Could not check @website/en language.")