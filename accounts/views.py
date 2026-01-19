from django.shortcuts import render, redirect
from django.contrib.auth import login, get_user_model
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import SignupForm

User = get_user_model()


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
        
        # ゲストプレイヤーからの変換処理
        converting_guest_player_id = self.request.session.get('converting_guest_player_id')
        if converting_guest_player_id:
            from game.models import Player
            try:
                guest_player = Player.objects.get(id=converting_guest_player_id, is_guest=True)
                # ゲストプレイヤーをこのユーザーに関連付け
                guest_player.user = user
                guest_player.is_guest = False
                guest_player.save()
                
                # セッションから削除
                del self.request.session['converting_guest_player_id']
                
                # ゲストプレイヤーのホーム画面にリダイレクト
                self.success_url = reverse_lazy('game:battle_start', kwargs={'player_id': guest_player.id})
            except Player.DoesNotExist:
                pass  # ゲストプレイヤーが見つからない場合は通常の処理
        
        return response

