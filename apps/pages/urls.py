from django.urls import path
from . import views

app_name = 'pages'

urlpatterns = [
    path('about/', views.about_view, name='about'),
    path('help-center/', views.help_center_view, name='help_center'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service_view, name='terms_of_service'),
]
