from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/withdraw/', views.withdraw, name='withdraw'),
    path('profile/transactions/', views.transaction_history, name='transaction_history'),
    path('profile/transactions/download/', views.download_transaction_statement, name='download_transaction_statement'),
    path('profile/<int:user_id>/', views.public_profile, name='public_profile'),
]