from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from .models import PatientBloodRequest, Profile
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
            'gender': forms.Select(choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')]),
            'blood_group': forms.Select(choices=[
                ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
                ('O+', 'O+'), ('O-', 'O-'), ('AB+', 'AB+'), ('AB-', 'AB-')
            ]),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    # 🔹 Custom validation for donor eligibility
    def clean(self):
        cleaned_data = super().clean()
        age = cleaned_data.get('age')
        weight = cleaned_data.get('weight')

        # Validate age and weight
        if age is not None and age < 18:
            raise forms.ValidationError("❌ You must be at least 18 years old to donate blood.")
        if weight is not None and weight < 50:
            raise forms.ValidationError("❌ You must weigh at least 50 kg to donate blood.")

        return cleaned_data


# ------------------ Patient Form ------------------
class PatientForm(forms.ModelForm):
    class Meta:
        model = PatientProfile
        fields = [
            'full_name', 'age', 'gender', 'blood_group', 'contact_number',
            'email', 'address',
            'hospital_name', 'disease_condition',
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
        fields = ['blood_group', 'units_requested', 'date_required', 'is_emergency']
        widgets = {
            'blood_group': forms.Select(choices=[
                ('A+', 'A+'), ('A-', 'A-'),
                ('B+', 'B+'), ('B-', 'B-'),
                ('O+', 'O+'), ('O-', 'O-'),
                ('AB+', 'AB+'), ('AB-', 'AB-'),
            ]),
            'date_required': forms.DateInput(attrs={'type': 'date'}),
        }
        
class PatientBloodRequestForm(forms.ModelForm):
    class Meta:
        model = PatientBloodRequest
        fields = ['units_Requested', 'hospital_Name','date_Required', 'is_Emergency']
        widgets = {'date_Required': forms.DateInput(attrs={'type':'date'})}

class HospitalBloodRequestForm(forms.ModelForm):
    class Meta:
        model = BloodRequest
        fields = ['blood_group', 'units_requested', 'date_required', 'is_emergency']
        widgets = {
            'blood_group': forms.Select(attrs={'class': 'form-select'}),
            'units_requested': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'date_required': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_emergency': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class BloodDonationCampForm(forms.ModelForm):
    class Meta:
        model = BloodDonationCamp
        fields = ['camp_name', 'date', 'venue', 'organizer', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }


# ------------------ Donor Appointment Request Form ------------------
class DonorAppointmentRequestForm(forms.Form):
    q1 = forms.CharField(
        label="Have you donated blood before? If yes, when was your last donation?",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Type date (YYYY-MM-DD) or No'})
    )
    q2 = forms.ChoiceField(label="Are you currently taking any medications?", choices=[('Yes', 'Yes'), ('No', 'No')], widget=forms.RadioSelect)
    q3 = forms.ChoiceField(label="Have you had any major surgeries recently?", choices=[('Yes', 'Yes'), ('No', 'No')], widget=forms.RadioSelect)
    q4 = forms.ChoiceField(label="Do you have any chronic diseases (like diabetes, hypertension, or heart problems)?", choices=[('Yes', 'Yes'), ('No', 'No')], widget=forms.RadioSelect)
    q5 = forms.ChoiceField(label="Have you ever had jaundice, hepatitis, malaria, or HIV?", choices=[('Yes', 'Yes'), ('No', 'No')], widget=forms.RadioSelect)
    q6 = forms.CharField(label="Have you been vaccinated recently? (If yes, when and which vaccine?)", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Write vaccine name or say No'}))
    q7 = forms.ChoiceField(label="Do you have any allergies or bleeding disorders?", choices=[('Yes', 'Yes'), ('No', 'No')], widget=forms.RadioSelect)
    q8 = forms.CharField(label="Have you ever received a blood transfusion? If yes, when?", widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Write date or say No'}))
    q9 = forms.ChoiceField(label="Have you recently traveled to an area with malaria or other infectious diseases?", choices=[('Yes', 'Yes'), ('No', 'No')], widget=forms.RadioSelect)
    q10 = forms.ChoiceField(label="Do you smoke, drink alcohol, or use recreational drugs?", choices=[('Yes', 'Yes'), ('No', 'No')], widget=forms.RadioSelect)
    q11 = forms.ChoiceField(label="Have you had any tattoos, piercings, or acupuncture in the past 6–12 months?", choices=[('Yes', 'Yes'), ('No', 'No')], widget=forms.RadioSelect)
    q12 = forms.ChoiceField(label="Have you had any recent illnesses, fever, or infections?", choices=[('Yes', 'Yes'), ('No', 'No')], widget=forms.RadioSelect)
    q13 = forms.ChoiceField(label="Are you currently pregnant, breastfeeding, or menstruating? (for female donors)", choices=[('Yes', 'Yes'), ('No', 'No'), ('Not Applicable', 'Not Applicable')], widget=forms.RadioSelect)

    def clean_q1(self):
        last_donation = self.cleaned_data['q1'].strip()

        if last_donation.lower() == 'no':
            return last_donation  # no previous donation, valid

        try:
            last_donation_date = datetime.strptime(last_donation, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError("Please enter a valid date in YYYY-MM-DD format or 'No'.")

        today = datetime.today().date()
        three_months_ago = today - timedelta(days=90)

        if last_donation_date > three_months_ago:
            raise ValidationError("You can only request after 3 months from your last donation.")

        return last_donation

class DonationDateForm(forms.Form):
    donation_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    donation_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))