from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # API endpoints for pro subscriptions
    path('api/initiate-subscription/', views.InitiateSubscriptionView.as_view(), name='initiate_subscription'),
    path('api/callback/subscription/', views.SubscriptionCallbackView.as_view(), name='subscription_callback'),
    path('api/status/<str:checkout_request_id>/', views.SubscriptionStatusView.as_view(), name='subscription_status'),
]