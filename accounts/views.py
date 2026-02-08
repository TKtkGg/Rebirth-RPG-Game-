from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, get_user_model
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import SignupForm
from game.scorepoints_content import build_score_bonus_defaults

User = get_user_model()


def home(request):
    """アカウントシステムのホーム画面"""
    return render(request, 'accounts/home.html')


def custom_logout(request):
    """カスタムログアウト処理（ゲストプレイヤーデータを削除）"""
    if request.method == 'POST':
        # セッションからゲストプレイヤーIDを取得
        guest_player_id = request.session.get('guest_player_id')
        
        if guest_player_id:
            # ゲストプレイヤーのデータを削除
            from game.models import Player
            try:
                player = Player.objects.get(id=guest_player_id, is_guest=True)
                player.delete()
            except Player.DoesNotExist:
                pass
            
            # セッションから削除
            if 'guest_player_id' in request.session:
                del request.session['guest_player_id']
        
        # ログアウト処理
        logout(request)
        
        # アカウントホーム画面にリダイレクト
        return redirect('accounts:home')
    
    return redirect('accounts:home')


class SignupView(CreateView):
    model = User
    form_class = SignupForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('game:start')  # 職業選択画面へ
    
    def form_valid(self, form):
        # ユーザーを作成
        response = super().form_valid(form)
        
        # 作成したユーザーでログイン
        user = self.object
        login(self.request, user)

        if not user.score_bonus_all and not user.score_bonus_jobs:
            score_bonus_all, score_bonus_jobs = build_score_bonus_defaults()
            user.score_bonus_all = score_bonus_all
            user.score_bonus_jobs = score_bonus_jobs
            user.save()
        
        # ゲストプレイヤーからの変換処理
        converting_guest_player_id = self.request.session.get('converting_guest_player_id')
        fallback_guest_player_id = self.request.session.get('guest_player_id')
        guest_player_id = converting_guest_player_id or fallback_guest_player_id
        if guest_player_id:
            from game.models import Player
            try:
                guest_player = Player.objects.get(id=guest_player_id, is_guest=True)
                # ゲストプレイヤーをこのユーザーに関連付け
                guest_player.user = user
                guest_player.is_guest = False
                guest_player.save()
                
                # セッションから削除
                if 'converting_guest_player_id' in self.request.session:
                    del self.request.session['converting_guest_player_id']
                if 'guest_player_id' in self.request.session:
                    del self.request.session['guest_player_id']
                
                # ゲストプレイヤーのホーム画面にリダイレクト
                self.success_url = reverse_lazy('game:battle_start', kwargs={'player_id': guest_player.id})
            except Player.DoesNotExist:
                pass  # ゲストプレイヤーが見つからない場合は通常の処理
        
        return response

