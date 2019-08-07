from django.db import models

class Language(models.Model):
	host = models.CharField(max_length=30, default="@website")
	default = models.BooleanField(default=False)

	code = models.CharField(max_length=2)
	name = models.CharField(max_length=30)

	access = models.SmallIntegerField() # For @website languages, this would be 75 (first, second, fourth, seventh)
	"""Works with right-to-left bitwise operations.
	First bit is if anyone can check fields.
	Second bit is if translators can check fields/suggestions and suggest changes.
	Third bit is if module staff can check fields/suggestions and suggest changes. This is ignored if host is @website
	Fourth bit is if moderators can check fields/suggestions and suggest changes.
	Fifth bit is if translators can edit suggestions.
	Sixth bit is if module staff can edit suggestions. This is ignored if host is @website
	Seventh bit is if moderators can edit suggestions.
	Module owners (or Bolodefchoco, if host is @website) can ALWAYS check/edit suggestions/fields."""

class LanguageField(models.Model):
	state = models.SmallIntegerField() # 0 -> not checked | 1 -> rejected | 2 -> not used | 3 -> accepted
	# Only module owners (the ones with the right to edit suggestions, if host is @website) can delete fields

	owner_id = models.BigIntegerField()
	state_id = models.BigIntegerField()

	host = models.CharField(max_length=30, default="@website")
	language = models.CharField(max_length=2)

	field = models.CharField(max_length=1000)
	value = models.CharField(max_length=1000000000)