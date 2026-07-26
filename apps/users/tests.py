from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

User = get_user_model()


@override_settings(DEBUG=True)
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


class RegistrationAntiSpamTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('users:register')

    def test_registration_rejects_suspicious_phone_number(self):
        response = self.client.post(self.register_url, {
            'phone_number': '+1-483-775-5009',
            'email': 'validuser@example.com',
            'username': 'legituser',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'terms_of_service': True,
            'website_url': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'phone_number', 'Invalid phone number area code provided.')

    def test_registration_rejects_disposable_email(self):
        response = self.client.post(self.register_url, {
            'phone_number': '0711002233',
            'email': 'nvhvskjr@immenseignite.info',
            'username': 'kqxwjiwndv',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'terms_of_service': True,
            'website_url': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'email', 'Registration using disposable email addresses is not permitted.')

    def test_registration_rejects_honeypot_spambot(self):
        response = self.client.post(self.register_url, {
            'phone_number': '0711002233',
            'email': 'spambot@example.com',
            'username': 'botuser',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'terms_of_service': True,
            'website_url': 'http://spam-link.com'  # Honeypot filled by bot
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], None, 'Spam submission detected.')

    def test_valid_registration_and_phone_normalization(self):
        response = self.client.post(self.register_url, {
            'phone_number': '0712345678',
            'email': 'newvaliduser@example.com',
            'username': 'validuser1',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'terms_of_service': True,
            'website_url': ''
        })
        self.assertRedirects(response, reverse('users:login'))
        created_user = User.objects.get(username='validuser1')
        self.assertEqual(created_user.phone_number, '+254712345678')


class PhoneLoginFlexibleTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('users:login')
        # User registered with +254... format
        self.user_plus = User.objects.create_user(
            phone_number="+254799887766",
            username="userplus",
            password="MySecretPass123!"
        )

    def test_login_with_local_07_format(self):
        # Registered as +254799887766, attempts login typing 0799887766
        response = self.client.post(self.login_url, {
            'phone_number': '0799887766',
            'password': 'MySecretPass123!'
        })
        self.assertRedirects(response, reverse('tips:marketplace'))

    def test_login_with_local_254_format(self):
        # Registered as +254799887766, attempts login typing 254799887766
        response = self.client.post(self.login_url, {
            'phone_number': '254799887766',
            'password': 'MySecretPass123!'
        })
        self.assertRedirects(response, reverse('tips:marketplace'))


