from django.urls import path
from django.contrib.auth.views import LoginView
from .views import SignupView, home, custom_logout
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', home, name='home'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', custom_logout, name='logout'),
    path('signup/', SignupView.as_view(), name='signup'),
]