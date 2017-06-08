from django.conf.urls import include, url
from rest_framework_mongoengine.routers import DefaultRouter

from . import views


router = DefaultRouter()
router.register(r'collections', views.CollectionViewSet)
router.register(r'documents', views.DocumentViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^ui/$', views.home),
]
