from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from .models import User, UserProfile


class RegistrationForm(UserCreationForm):
    """User registration form with phone number and user type"""
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '0712345678'
        })
    )
    username = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Optional username'
        })
    )
    # User roles - multiple selection allowed
    is_buyer = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )
    is_tipster = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Password'
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Confirm Password'
        })
    )
    terms_of_service = forms.BooleanField(
        required=True,
        initial=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
    )
    
    class Meta:
        model = User
        fields = ['phone_number', 'username', 'password1', 'password2']
    
    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if User.objects.filter(phone_number=phone_number).exists():
            raise forms.ValidationError("This phone number is already registered.")
        return phone_number

    def clean(self):
        cleaned_data = super().clean()
        is_buyer = cleaned_data.get('is_buyer')
        is_tipster = cleaned_data.get('is_tipster')

        # At least one role must be selected
        if not is_buyer and not is_tipster:
            raise forms.ValidationError("Please select at least one account type (Buyer or Tipster).")

        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.phone_number = self.cleaned_data['phone_number']
        if self.cleaned_data.get('username'):
            user.username = self.cleaned_data['username']

        if commit:
            user.save()
            # Set user roles in profile
            user.userprofile.is_buyer = self.cleaned_data.get('is_buyer', False)
            user.userprofile.is_tipster = self.cleaned_data.get('is_tipster', False)
            user.userprofile.save()

        return user


class LoginForm(forms.Form):
    """User login form using phone number"""
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': '0712345678'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Password'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        phone_number = cleaned_data.get('phone_number')
        password = cleaned_data.get('password')
        
        if phone_number and password:
            user = authenticate(username=phone_number, password=password)
            if not user:
                raise forms.ValidationError("Invalid phone number or password.")
            elif not user.is_active:
                raise forms.ValidationError("This account is inactive.")
        
        return cleaned_data


class ProfileEditForm(forms.ModelForm):
    """Form for editing user profile"""
    username = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Username'
        })
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Email address'
        })
    )
    
    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_picture']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'Tell us about yourself...'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-input',
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