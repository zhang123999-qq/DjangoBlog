from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('search/', views.search_view, name='search'),
    path('healthz/', views.healthz_view, name='healthz'),
    path('contact/', views.contact_view, name='contact'),
]
