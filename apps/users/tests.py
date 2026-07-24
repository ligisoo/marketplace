from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

User = get_user_model()


class PasswordResetTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            phone_number="254711223344",
            username="betatester",
            email="beta@example.com",
            password="oldpassword123"
        )
        self.reset_url = reverse('users:password_reset')

    def test_password_reset_request_by_phone(self):
        response = self.client.post(self.reset_url, {'identifier': '254711223344'})
        self.assertRedirects(response, reverse('users:password_reset_done'))
        
        # Verify session link generation
        self.assertIn('beta_password_reset_url', self.client.session)

    def test_password_reset_request_by_email(self):
        response = self.client.post(self.reset_url, {'identifier': 'beta@example.com'})
        self.assertRedirects(response, reverse('users:password_reset_done'))
        self.assertIn('beta_password_reset_url', self.client.session)

    def test_password_reset_confirm_and_login(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        confirm_url = reverse('users:password_reset_confirm', kwargs={'uidb64': uid, 'token': token})

        # GET confirm page
        response = self.client.get(confirm_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['validlink'])

        # POST new password
        post_response = self.client.post(confirm_url, {
            'new_password1': 'newsecurepass123',
            'new_password2': 'newsecurepass123'
        })
        self.assertRedirects(post_response, reverse('users:password_reset_complete'))

        # Verify old password fails and new password succeeds
        login_failed = self.client.login(username="254711223344", password="oldpassword123")
        self.assertFalse(login_failed)

        login_success = self.client.login(username="254711223344", password="newsecurepass123")
        self.assertTrue(login_success)
