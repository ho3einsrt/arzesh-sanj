from django.urls import path
from calculator.views import calculation
urlpatterns = [path('api/calculate/', calculation)]
