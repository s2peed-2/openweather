from django.contrib import admin
from django.urls import path
from weather import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.weather_view, name='weather'),
    path('storms/', views.storm_map, name='storms'),
    path('tiles/<str:layer>/<int:z>/<int:x>/<int:y>.png', views.weather_tile, name='tile'),
    path('api/point/', views.point_api, name='point_api'),
]