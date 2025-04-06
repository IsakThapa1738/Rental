from django import forms
from .models import Booking
from django.core.exceptions import ValidationError
import datetime

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['check_in', 'check_out']
        widgets = {
            'check_in': forms.DateInput(attrs={'type': 'date'}),
            'check_out': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        check_in = cleaned_data.get('check_in')
        check_out = cleaned_data.get('check_out')
        
        if check_in and check_out:
            # Check if check_out is after check_in
            if check_out <= check_in:
                raise ValidationError("Check-out date must be after check-in date")
            
            # Check if dates are in the future
            today = datetime.date.today()
            if check_in < today:
                raise ValidationError("Check-in date cannot be in the past")
        
        return cleaned_data