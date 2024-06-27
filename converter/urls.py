from django.urls import path
from .views import donate_view
from .views import signup_view
from .views import login_view
from .views import upload_file
from . import views

urlpatterns = [
    path('donate/', views.donate_view, name='donate' ),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('upload/', views.upload_file, name='upload'),
]
