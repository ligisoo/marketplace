import re
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from .models import User, UserProfile

DISPOSABLE_EMAIL_DOMAINS = {
    'immenseignite.info', 'tempmail.com', '10minutemail.com', 'guerrillamail.com',
    'mailinator.com', 'throwawaymail.com', 'trashmail.com', 'sharklasers.com',
    'dispostable.com', 'getnada.com', 'bupkis.org', 'yopmail.com'
}


class RegistrationForm(UserCreationForm):
    """User registration form with phone number, email, username and anti-spam protection"""
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full block px-4 py-3 bg-secondary/80 border border-border rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all text-sm',
            'placeholder': '0712345678'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input w-full block px-4 py-3 bg-secondary/80 border border-border rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all text-sm',
            'placeholder': 'your-email@example.com'
        })
    )
    username = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full block px-4 py-3 bg-secondary/80 border border-border rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all text-sm',
            'placeholder': 'Optional username'
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input w-full block px-4 py-3 bg-secondary/80 border border-border rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all text-sm',
            'placeholder': 'Password'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input w-full block px-4 py-3 bg-secondary/80 border border-border rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all text-sm',
            'placeholder': 'Confirm Password'
        })
    )
    # Honeypot field - invisible to real human users, traps spam bots
    website_url = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'style': 'position: absolute; left: -9999px; opacity: 0; height: 0; width: 0;',
            'tabindex': '-1',
            'autocomplete': 'off'
        })
    )
    terms_of_service = forms.BooleanField(
        required=True,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox w-4 h-4 rounded border-border text-primary focus:ring-primary bg-secondary/80 cursor-pointer'}),
    )
    
    class Meta:
        model = User
        fields = ['phone_number', 'email', 'username', 'password1', 'password2']
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number', '').strip()
        cleaned_phone = re.sub(r'[\s\-\(\)]', '', phone_number)

        # Check basic digit and E.164 length structure
        if not re.match(r'^\+?[0-9]{8,15}$', cleaned_phone):
            raise forms.ValidationError("Please enter a valid phone number (e.g. 0712345678 or +254712345678).")

        # Explicitly reject invalid NANP area codes (e.g. +1-483...)
        if cleaned_phone.startswith('+1483') or cleaned_phone.startswith('1483'):
            raise forms.ValidationError("Invalid phone number area code provided.")

        # Standardize Kenyan phone formats (0712345678 / 0112345678 / 2547...) to +254...
        if re.match(r'^(07|01)\d{8}$', cleaned_phone):
            cleaned_phone = '+254' + cleaned_phone[1:]
        elif re.match(r'^254(7|1)\d{8}$', cleaned_phone):
            cleaned_phone = '+' + cleaned_phone

        if User.objects.filter(phone_number=cleaned_phone).exists():
            raise forms.ValidationError("This phone number is already registered.")
        return cleaned_phone

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if not email:
            return email

        domain = email.split('@')[-1]
        if domain in DISPOSABLE_EMAIL_DOMAINS:
            raise forms.ValidationError("Registration using disposable email addresses is not permitted.")

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email address is already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        honeypot = cleaned_data.get('website_url')
        if honeypot:
            raise forms.ValidationError("Spam submission detected.")
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.phone_number = self.cleaned_data['phone_number']
        user.email = self.cleaned_data['email']
        if self.cleaned_data.get('username'):
            user.username = self.cleaned_data['username']

        if commit:
            user.save()

        return user



def get_phone_variants(phone_input):
    """
    Generate phone format variants (e.g. +254712345678, 0712345678, 254712345678)
    so authentication and user lookup succeed regardless of how the user typed or registered their phone number.
    """
    if not phone_input:
        return []
    
    raw = phone_input.strip()
    cleaned = re.sub(r'[\s\-\(\)]', '', raw)
    candidates = [raw, cleaned]

    if re.match(r'^(07|01)\d{8}$', cleaned):
        e164 = '+254' + cleaned[1:]
        local_254 = '254' + cleaned[1:]
        candidates.extend([e164, local_254])
    elif re.match(r'^\+254(7|1)\d{8}$', cleaned):
        local_0 = '0' + cleaned[4:]
        local_254 = cleaned[1:]
        candidates.extend([local_0, local_254])
    elif re.match(r'^254(7|1)\d{8}$', cleaned):
        e164 = '+' + cleaned
        local_0 = '0' + cleaned[3:]
        candidates.extend([e164, local_0])

    seen = set()
    result = []
    for c in candidates:
        if c and c not in seen:
            seen.add(c)
            result.append(c)
    return result


class LoginForm(forms.Form):
    """User login form supporting multiple phone number formats"""
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full block px-4 py-3 bg-secondary/80 border border-border rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all text-sm',
            'placeholder': '0712345678 or +254712345678'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input w-full block px-4 py-3 bg-secondary/80 border border-border rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all text-sm',
            'placeholder': 'Password'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        phone_number = cleaned_data.get('phone_number')
        password = cleaned_data.get('password')
        
        if phone_number and password:
            candidates = get_phone_variants(phone_number)
            user = None
            for candidate in candidates:
                user = authenticate(username=candidate, password=password)
                if user:
                    break

            if not user:
                raise forms.ValidationError("Invalid phone number or password.")
            elif not user.is_active:
                raise forms.ValidationError("This account is inactive.")
            
            self.user_cache = user
        
        return cleaned_data

    def get_user(self):
        return getattr(self, 'user_cache', None)


class ProfileEditForm(forms.ModelForm):
    """Form for editing user profile"""
    username = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full block px-4 py-3 bg-secondary/80 border border-border rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all text-sm',
            'placeholder': 'Username'
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-input w-full block px-4 py-3 bg-secondary/80 border border-border rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all text-sm',
            'placeholder': 'Email address'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-textarea w-full block p-4 bg-secondary/80 border border-border rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all text-sm',
                'rows': 4,
                'placeholder': 'Tell us about yourself...'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-input w-full block p-2 bg-secondary/80 border border-border rounded-xl text-foreground file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-primary-foreground hover:file:bg-primary/90 text-sm cursor-pointer',
                'accept': 'image/*'
            })
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email
    
    def save(self, commit=True):
        profile = super().save(commit=False)
        
        if self.user:
            # Update user fields
            self.user.username = self.cleaned_data.get('username')
            self.user.email = self.cleaned_data.get('email')
            
            if commit:
                self.user.save()
                profile.save()
        
        return profile


class CustomPasswordResetForm(forms.Form):
    """Form to request password reset by phone number or email"""
    identifier = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-input w-full block px-4 py-3 bg-secondary/80 border border-border rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all text-sm',
            'placeholder': 'Phone number (e.g. 0712345678) or Email'
        })
    )

    def clean_identifier(self):
        identifier = self.cleaned_data.get('identifier', '').strip()
        if not identifier:
            raise forms.ValidationError("Please enter your registered phone number or email address.")
        return identifier

    def get_user(self):
        identifier = self.cleaned_data.get('identifier', '').strip()
        if '@' in identifier:
            return User.objects.filter(email__iexact=identifier).first()
        
        candidates = get_phone_variants(identifier)
        for candidate in candidates:
            user = User.objects.filter(phone_number=candidate).first()
            if user:
                return user
        return None


class CustomSetPasswordForm(forms.Form):
    """Form to set a new password during password reset"""
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input w-full block px-4 py-3 bg-secondary/80 border border-border rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all text-sm',
            'placeholder': 'New Password'
        })
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input w-full block px-4 py-3 bg-secondary/80 border border-border rounded-xl text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all text-sm',
            'placeholder': 'Confirm New Password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')

        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("The two password fields didn't match.")
        if p1 and len(p1) < 6:
            raise forms.ValidationError("Password must be at least 6 characters long.")
        return cleaned_data