from .models import Project, ProjectUser

ADMINISTRATOR = (1 << 0)
CREATE_LANGUAGE = (1 << 1)
EDIT_DESCRIPTION = (1 << 2)
EDIT_NAME = (1 << 3)
EDIT_PUB_STATE = (1 << 4)
ADD_NEW_MEMBERS = (1 << 5)
REMOVE_MEMBERS = (1 << 6)
EDIT_PERMISSIONS = (1 << 7)

def get_projects_by_user(user, owner=None):
	if owner is None:
		user_queryset = ProjectUser.objects.filter(id=user)
	else:
		user_queryset = ProjectUser.objects.filter(id=user, owner=owner)
	projects_filter = []

	for user in user_queryset:
		projects_filter.append(user.project)

	return Project.objects.filter(name__in=projects_filter)

def get_project(project):
	if isinstance(project, str):
		try:
			project = Project.objects.get(name__iexact=project)
		except Project.DoesNotExist:
			return None

	return project

def get_project_users(project):
	if not isinstance(project, str):
		project = project.name

	return ProjectUser.objects.filter(project__iexact=project)

def get_project_user(project, user):
	if not isinstance(project, str):
		project = project.name

	try:
		return ProjectUser.objects.get(project__iexact=project, id=user)
	except ProjectUser.DoesNotExist:
		return None