from django.urls import path
from portfolio_rag_bot.api.views import ChatStreamView

urlpatterns = [
    path('chat/', ChatStreamView.as_view(), name='chat'),
]
