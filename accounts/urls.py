from django.urls import path
from django.contrib.auth.views import LogoutView, LoginView
from .views import SignupView, home
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', home, name='home'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('signup/', SignupView.as_view(), name='signup'),
]