"""fsol URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include

import api.views
import common.views

urlpatterns = [
    re_path(r"^api/v(?P<version>\d+)/(?P<path>.+)$", api.views.view),
	re_path(r"^api/(?P<path>.+)$", api.views.default_view),
	re_path(r"^static/+(?P<path>.+)$", common.views.Static().view),
	common.views.HomeTemplate().as_url(),
    common.views.AnnouncementsTemplate().as_url(),
    common.views.MembersTemplate().as_url(),
    common.views.SpecificMemberTemplate().as_url(),
]
