from django.urls import path
from . import views

app_name = 'tips'

urlpatterns = [
    # Marketplace
    path('', views.marketplace, name='marketplace'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('<int:tip_id>/', views.tip_detail, name='detail'),

    # Tipster views
    path('my-tips/', views.my_tips, name='my_tips'),
    path('earnings/', views.earnings_dashboard, name='earnings'),
    path('earnings/download/', views.download_earnings_statement, name='download_earnings_statement'),
    # path("earnings/export.csv", views.earnings_export_csv, name="earnings_export_csv"),
    path('create/', views.create_tip, name='create_tip'),
    path('verify/<int:tip_id>/', views.verify_tip, name='verify_tip'),
    path('processing/<int:tip_id>/', views.tip_processing_status, name='tip_processing_status'),

    # Purchase
    path('purchase/<int:tip_id>/', views.purchase_tip, name='purchase_tip'),

    # Tipster profiles
    path('tipster/<int:tipster_id>/', views.tipster_profile, name='tipster_profile'),
]