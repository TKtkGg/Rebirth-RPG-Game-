from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import SignupForm

def home(request):
    """アカウントシステムのホーム画面"""
    return render(request, 'accounts/home.html')

class SignupView(CreateView):
    model = User
    form_class = SignupForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('game:start')  # 職業選択画面へ
    
    def form_valid(self, form):
        # ユーザーを作成
        response = super().form_valid(form)
        
        # 作成したユーザーでログイン
        user = form.save()
        login(self.request, user)
        
        # Playerは職業選択後に作成する（ここでは作成しない）
        
        return response

