from django.db import models

class ProjectUser(models.Model):
	id = models.BigIntegerField(primary_key=True)
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

class Project(models.Model):
	name = models.CharField(max_length=29)
	description = models.CharField(max_length=1000000000, default="")
	public = models.BooleanField(default=False)