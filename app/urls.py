from django.urls import path
from . import views

urlpatterns = [
    path('digest/<str:username>/', views.digest_view, name='digest-view'),
]