from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from payments.models import PromoCode, PromoCodeRedemption

User = get_user_model()


class PromoCodeModelTestCase(TestCase):
    def setUp(self):
        self.promo = PromoCode.objects.create(
            code="beta2026",  # Testing auto-uppercase
            pro_duration_days=30,
            max_uses=2,
            is_active=True
        )

    def test_promo_code_uppercase(self):
        self.assertEqual(self.promo.code, "BETA2026")

    def test_promo_code_validity(self):
        self.assertTrue(self.promo.is_valid)

        # Deactivate
        self.promo.is_active = False
        self.assertFalse(self.promo.is_valid)
        self.promo.is_active = True

        # Max uses reached
        self.promo.used_count = 2
        self.assertFalse(self.promo.is_valid)
        self.promo.used_count = 0

        # Expired
        self.promo.expires_at = timezone.now() - timedelta(days=1)
        self.assertFalse(self.promo.is_valid)


class PromoCodeRedemptionViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            phone_number="254700000000",
            username="testuser",
            password="password123"
        )
        self.promo = PromoCode.objects.create(
            code="BETA2026",
            pro_duration_days=30,
            max_uses=10,
            is_active=True
        )
        self.url = reverse('payments:redeem_promo')

    def test_redeem_promo_code_success(self):
        self.client.login(username="254700000000", password="password123")
        response = self.client.post(self.url, {'code': 'beta2026'})
        
        # User profile should now be pro
        self.user.userprofile.refresh_from_db()
        self.assertTrue(self.user.userprofile.is_pro)
        self.assertTrue(self.user.userprofile.is_pro_active)
        
        # Promo used count should increment
        self.promo.refresh_from_db()
        self.assertEqual(self.promo.used_count, 1)

        # Redemption record created
        self.assertTrue(PromoCodeRedemption.objects.filter(promo_code=self.promo, user=self.user).exists())

    def test_prevent_duplicate_redemption(self):
        self.client.login(username="254700000000", password="password123")
        
        # First redemption
        self.client.post(self.url, {'code': 'BETA2026'})
        
        # Second redemption attempt
        response = self.client.post(self.url, {'code': 'BETA2026'})
        
        self.promo.refresh_from_db()
        self.assertEqual(self.promo.used_count, 1)

    def test_invalid_promo_code(self):
        self.client.login(username="254700000000", password="password123")
        response = self.client.post(self.url, {'code': 'INVALIDCODE'})
        
        self.user.userprofile.refresh_from_db()
        self.assertFalse(self.user.userprofile.is_pro)
