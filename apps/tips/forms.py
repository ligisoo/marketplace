from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from datetime import timedelta
from .models import Tip, TipMatch
from .ocr import BetslipOCR


class TipSubmissionForm(forms.ModelForm):
    """Form for initial tip submission with betslip upload or sharing link"""

    # MVP1: Only SportPesa available
    # To enable more bookmakers, uncomment the ones below:
    AVAILABLE_BOOKMAKERS = [
        ('sportpesa', 'SportPesa'),
        # ('betika', 'Betika'),      # Coming soon
        # ('odibets', 'Odibets'),    # Coming soon
        # ('mozzart', 'Mozzart'),    # Coming soon
        # ('betin', 'Betin'),        # Coming soon
        # ('other', 'Other'),        # Coming soon
    ]

    bet_code = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your bet code (e.g., JYRCAV)',
            'style': 'text-transform: uppercase;'
        }),
        help_text='Enter the bet code from your betslip'
    )

    class Meta:
        model = Tip
        fields = ['bookmaker', 'bet_code', 'price', 'screenshot']
        widgets = {
            'bookmaker': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Tip price in KES',
                'min': '1',
                'step': '1'
            }),
            'screenshot': forms.FileInput(attrs={
                'class': 'form-input',
                'accept': 'image/*',
                'required': True
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Override bookmaker choices to only show available ones
        self.fields['bookmaker'].choices = self.AVAILABLE_BOOKMAKERS
    
    def clean_bet_code(self):
        bet_code = self.cleaned_data.get('bet_code', '').strip().upper()
        if bet_code:
            # Check if bet code already exists
            if Tip.objects.filter(bet_code=bet_code).exists():
                raise ValidationError("A tip with this bet code already exists. Please check your bet code.")
        return bet_code

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price < 1:
            raise ValidationError("Minimum tip price is KES 1")
        if price and price > 1000:
            raise ValidationError("Maximum tip price is KES 1,000")
        return price
    
    def clean_screenshot(self):
        screenshot = self.cleaned_data.get('screenshot')
        if screenshot:
            # Check file size (max 5MB)
            if screenshot.size > 5 * 1024 * 1024:
                raise ValidationError("Image file too large (max 5MB)")

            # Check file type
            if not screenshot.content_type.startswith('image/'):
                raise ValidationError("File must be an image")

        return screenshot

    def clean(self):
        cleaned_data = super().clean()
        screenshot = cleaned_data.get('screenshot')

        # Screenshot is required for synchronous processing
        if not screenshot:
            raise ValidationError({
                'screenshot': 'Please upload a betslip screenshot.'
            })

        return cleaned_data


class TipVerificationForm(forms.Form):
    """Form for verifying and editing OCR-extracted data"""
    
    bet_code = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Bet code from your betslip'
        })
    )
    
    total_odds = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Total odds (e.g., 3.45)',
            'step': '0.01'
        })
    )
    
    expires_at = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-input',
            'type': 'datetime-local'
        }),
        help_text="When does this tip expire? (latest match kick-off time)"
    )
    
    def __init__(self, *args, **kwargs):
        self.ocr_data = kwargs.pop('ocr_data', {})
        self.matches_data = kwargs.pop('matches_data', [])
        super().__init__(*args, **kwargs)
        
        # Pre-populate with OCR data if available
        if self.ocr_data:
            self.fields['bet_code'].initial = self.ocr_data.get('bet_code', '')
            self.fields['total_odds'].initial = self.ocr_data.get('total_odds', '')

            # Parse expires_at from ISO string if present
            expires_at = self.ocr_data.get('expires_at')
            if isinstance(expires_at, str):
                expires_at = parse_datetime(expires_at)
            self.fields['expires_at'].initial = expires_at or (timezone.now() + timedelta(hours=24))
        
        # Add dynamic match fields
        for i, match in enumerate(self.matches_data):
            self._add_match_fields(i, match)
    
    def _add_match_fields(self, index, match_data):
        """Add fields for each match"""
        prefix = f'match_{index}_'
        
        self.fields[f'{prefix}home_team'] = forms.CharField(
            label=f'Match {index + 1} - Home Team',
            initial=match_data.get('home_team', ''),
            widget=forms.TextInput(attrs={'class': 'form-input'})
        )
        
        self.fields[f'{prefix}away_team'] = forms.CharField(
            label='Away Team',
            initial=match_data.get('away_team', ''),
            widget=forms.TextInput(attrs={'class': 'form-input'})
        )

        self.fields[f'{prefix}market'] = forms.CharField(
            label='Betting Market',
            initial=match_data.get('market', ''),
            widget=forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Over 2.5, 1X2, BTTS'
            })
        )
        
        self.fields[f'{prefix}selection'] = forms.CharField(
            label='Selection',
            initial=match_data.get('selection', ''),
            widget=forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Over, 1, Yes'
            })
        )
        
        self.fields[f'{prefix}odds'] = forms.DecimalField(
            label='Odds',
            initial=match_data.get('odds', ''),
            max_digits=6,
            decimal_places=2,
            widget=forms.NumberInput(attrs={
                'class': 'form-input',
                'step': '0.01'
            })
        )
        
        # Parse match_date from ISO string if present
        match_date = match_data.get('match_date')
        if isinstance(match_date, str):
            match_date = parse_datetime(match_date)

        self.fields[f'{prefix}match_date'] = forms.DateTimeField(
            label='Match Date & Time',
            initial=match_date or (timezone.now() + timedelta(hours=24)),
            widget=forms.DateTimeInput(attrs={
                'class': 'form-input',
                'type': 'datetime-local'
            })
        )
    
    def clean_bet_code(self):
        bet_code = self.cleaned_data.get('bet_code')
        if bet_code:
            # Check if bet code already exists
            if Tip.objects.filter(bet_code=bet_code).exists():
                raise ValidationError("A tip with this bet code already exists")
        return bet_code
    
    def clean_expires_at(self):
        expires_at = self.cleaned_data.get('expires_at')
        if expires_at:
            if expires_at <= timezone.now():
                raise ValidationError("Expiry time must be in the future")
            
            # Check if expiry is too far in the future (max 7 days)
            if expires_at > timezone.now() + timedelta(days=7):
                raise ValidationError("Expiry time cannot be more than 7 days from now")
        
        return expires_at
    
    def get_matches_data(self):
        """Extract matches data from cleaned form data"""
        matches = []
        i = 0
        
        while f'match_{i}_home_team' in self.cleaned_data:
            match_data = {
                'home_team': self.cleaned_data[f'match_{i}_home_team'],
                'away_team': self.cleaned_data[f'match_{i}_away_team'],
                'league': 'Unknown League',  # Default value since field removed
                'market': self.cleaned_data[f'match_{i}_market'],
                'selection': self.cleaned_data[f'match_{i}_selection'],
                'odds': self.cleaned_data[f'match_{i}_odds'],
                'match_date': self.cleaned_data[f'match_{i}_match_date'],
            }
            matches.append(match_data)
            i += 1
        
        return matches


class TipSearchForm(forms.Form):
    """Form for searching and filtering tips in marketplace"""

    # MVP1: Only SportPesa available
    AVAILABLE_BOOKMAKERS = [
        ('sportpesa', 'SportPesa'),
        # ('betika', 'Betika'),      # Coming soon
        # ('odibets', 'Odibets'),    # Coming soon
        # ('mozzart', 'Mozzart'),    # Coming soon
        # ('betin', 'Betin'),        # Coming soon
        # ('other', 'Other'),        # Coming soon
    ]

    SORT_CHOICES = [
        ('-created_at', 'Newest First'),
        ('price', 'Price: Low to High'),
        ('-price', 'Price: High to Low'),
        ('-odds', 'Highest Odds'),
        ('expires_at', 'Expiring Soon'),
    ]

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Search tips, teams, tipsters...'
        })
    )

    bookmaker = forms.ChoiceField(
        choices=[('', 'All Bookmakers')] + AVAILABLE_BOOKMAKERS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    min_odds = forms.DecimalField(
        required=False,
        min_value=1.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Min odds',
            'step': '0.1'
        })
    )
    
    max_odds = forms.DecimalField(
        required=False,
        min_value=1.0,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Max odds',
            'step': '0.1'
        })
    )
    
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Min price (KES)',
            'step': '1'
        })
    )
    
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-input',
            'placeholder': 'Max price (KES)',
            'step': '1'
        })
    )
    
    sort_by = forms.ChoiceField(
        choices=SORT_CHOICES,
        required=False,
        initial='-created_at',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        
        min_odds = cleaned_data.get('min_odds')
        max_odds = cleaned_data.get('max_odds')
        if min_odds and max_odds and min_odds > max_odds:
            raise ValidationError('Minimum odds cannot be greater than maximum odds')
        
        min_price = cleaned_data.get('min_price')
        max_price = cleaned_data.get('max_price')
        if min_price and max_price and min_price > max_price:
            raise ValidationError('Minimum price cannot be greater than maximum price')
        
        return cleaned_data