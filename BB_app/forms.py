from django import forms
from django.contrib.auth.models import User
from .models import Profile
from .models import BloodStock, BloodRequest
from .models import Contact
from .models import DonorProfile, PatientProfile, HospitalProfile
from .models import BloodDonationCamp


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(
        choices=[('', '--- choose role ---')] + list(Profile.ROLE_CHOICES),
        required=True,
        label='Role'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        help_texts = {
            'username': None,   # removes "Required. 150 characters..." text
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data


class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['name', 'email', 'phone', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Full Name', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email Address', 'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'placeholder': 'Phone Number', 'class': 'form-control'}),
            'message': forms.Textarea(attrs={'placeholder': 'Your Message', 'rows': 5, 'class': 'form-control'}),
        }

    
class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(
        widget=forms.PasswordInput,
        label='New Password'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
        label='Confirm Password'
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data





# ------------------ Donor Form ------------------
class DonorForm(forms.ModelForm):
    class Meta:
        model = DonorProfile
        fields = [
            'full_name', 'age', 'gender', 'blood_group', 'address',
            'contact_number', 'email', 'profile_pic',
            'weight',
            ]
        widgets = {
            'gender': forms.Select(choices=[('Male','Male'),('Female','Female'),('Other','Other')]),
            'blood_group': forms.Select(choices=[('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),
                                                 ('O+','O+'),('O-','O-'),('AB+','AB+'),('AB-','AB-')]),
            'address': forms.Textarea(attrs={'rows':3}),
        }

# ------------------ Patient Form ------------------
class PatientForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = [
            'full_name', 'age', 'gender', 'blood_group_needed', 'contact_number',
            'email', 'address',
            'hospital_name', 'disease_condition', 'units_required',
            'date_required',
            'notes', 'prescription'
        ]
        widgets = {
            'gender': forms.Select(choices=[('Male','Male'),('Female','Female'),('Other','Other')]),
            'blood_group_needed': forms.Select(choices=[('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),
                                                        ('O+','O+'),('O-','O-'),('AB+','AB+'),('AB-','AB-')]),
            'address': forms.Textarea(attrs={'rows':3}),
            'disease_condition': forms.Textarea(attrs={'rows':2}),
            'notes': forms.Textarea(attrs={'rows':2}),
        }

# ------------------ Hospital Form ------------------
class HospitalForm(forms.ModelForm):
    class Meta:
        model = HospitalProfile
        fields = [
            'hospital_name', 'hospital_id', 'location',
            'contact', 'email', 'Hospital_Logo',
            'storage_capacity', 'requests',
            'license_upload',
        ]
        widgets = {
            'location': forms.Textarea(attrs={'rows': 3}),
            'requests': forms.Textarea(attrs={'rows': 3}),
            'Hospital_Logo': forms.ClearableFileInput(),
            'license_upload': forms.ClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove "Clear" text from image/file fields
        for field_name in ['Hospital_Logo', 'license_upload']:
            field = self.fields[field_name]
            field.widget.clear_checkbox_label = ''
            field.widget.initial_text = 'Currently'
            field.widget.input_text = ''  # removes "Change" text



class BloodStockForm(forms.ModelForm):
    class Meta:
        model = BloodStock
        fields = ['blood_group', 'units_available']


class BloodRequestForm(forms.ModelForm):
    class Meta:
        model = BloodRequest
        fields = ['patient_name', 'blood_group', 'units_requested', 'date_required', 'is_emergency']
        widgets = {
            'blood_group': forms.Select(choices=[
                ('A+', 'A+'), ('A-', 'A-'),
                ('B+', 'B+'), ('B-', 'B-'),
                ('O+', 'O+'), ('O-', 'O-'),
                ('AB+', 'AB+'), ('AB-', 'AB-'),
            ]),
            'date_required': forms.DateInput(attrs={'type': 'date'}),
        }
        


class BloodDonationCampForm(forms.ModelForm):
    class Meta:
        model = BloodDonationCamp
        fields = ['camp_name', 'date', 'venue', 'organizer', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

