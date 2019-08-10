from django.db import models

class ProjectUser(models.Model):
	row_id = models.AutoField(primary_key=True)
	id = models.BigIntegerField()
	role = models.CharField(max_length=100, default="")
	project = models.CharField(max_length=29)
	owner = models.BooleanField(default=False)
	public = models.BooleanField(default=True)
	permissions = models.SmallIntegerField(default=0)
	"""Works with right-to-left bitwise operations.
	Admin (has everything) / Delete project NOT included
	Create language
	Edit project description
	Edit project name
	Make the project public/private
	Add new members
	Remove members # The member to be removed must have the same or less permissions than this one.
	Edit member permissions # The member permissions must be the same or less than this one. The new permissions too. Can't self-edit permissions.
	"""

	class Meta:
		constraints = [
			models.UniqueConstraint(fields=["id", "project"], name="user identifier")
			#  This constraint makes that nobody can be twice in the project. Previously it
			# was being made by setting `id` (user id) as primary_key, but when the user
			# tried to belong to two projects, it threw an error, since the `id` column was
			# unique. Now this is defining `id` and `project` as a couple. If one of them
			# is repeated it won't throw any error (i.e: a user belonging to multiple
			# projects), but if both are repeated it will (the user can't belong two times
			# to the same project!)
		]

class Project(models.Model):
	name = models.CharField(max_length=29)
	description = models.CharField(max_length=1000000000, default="")
	public = models.BooleanField(default=False)