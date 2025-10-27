from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # API endpoints for tip payments
    path('api/initiate-tip-payment/', views.InitiateTipPaymentView.as_view(), name='initiate_tip_payment'),
    path('api/callback/', views.TipPaymentCallbackView.as_view(), name='tip_payment_callback'),
    path('api/status/<str:checkout_request_id>/', views.TipPaymentStatusView.as_view(), name='tip_payment_status'),
]