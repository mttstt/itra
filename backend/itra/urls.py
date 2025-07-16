"""
URL configuration for itra project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path, include

urlpatterns = [
    path('', include('homepage.urls')), # Homepage che mostra il README.md
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')), # core.urls ora sarà dedicato alle API
]

# Modifica il titolo e l'header del sito admin
admin.site.site_header = "IT Risk Administrator"
admin.site.site_title = "IT Risk Administrator Portal"
admin.site.index_title = "Benvenuto nel portale IT Risk Administrator"
