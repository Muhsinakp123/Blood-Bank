from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    

    ROLE_CHOICES = (
        ('donor', 'Donor'),
        ('hospital', 'Hospital'),
        ('patient', 'Patient'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.user} ({self.role})"
    
    
class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"

    
    
    
# ------------------ Donor Profile ------------------
class DonorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Personal Information
    full_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=[('Male','Male'),('Female','Female'),('Other','Other')])
    blood_group = models.CharField(max_length=3, choices=[('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),
                                                          ('O+','O+'),('O-','O-'),('AB+','AB+'),('AB-','AB-')])
    address = models.TextField()
    contact_number = models.CharField(max_length=15)
    email = models.EmailField()
    profile_pic = models.ImageField(upload_to='donor_profiles/', blank=True, null=True)
    
    # Health Information
    weight = models.FloatField()
    

    def __str__(self):
        return self.full_name


# ------------------ Patient Profile ------------------
class PatientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Personal Information
    full_name = models.CharField(max_length=100)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=10, choices=[('Male','Male'),('Female','Female'),('Other','Other')])
    blood_group = models.CharField(max_length=3, choices=[('A+','A+'),('A-','A-'),('B+','B+'),('B-','B-'),
                                                                 ('O+','O+'),('O-','O-'),('AB+','AB+'),('AB-','AB-')])
    contact_number = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    
    # Medical Information
    hospital_name = models.CharField(max_length=100, blank=True, null=True)
    disease_condition = models.TextField(blank=True, null=True)
    
    # Consent / Notes
    notes = models.TextField(blank=True, null=True)
    prescription = models.FileField(upload_to='prescriptions/', blank=True, null=True)

    def __str__(self):
        return self.full_name


# ------------------ Hospital Profile ------------------
class HospitalProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Hospital Information
    hospital_name = models.CharField(max_length=150)
    hospital_id = models.CharField(max_length=50)
    location = models.TextField()
    contact = models.CharField(max_length=15)
    email = models.EmailField()
    Hospital_Logo = models.ImageField(upload_to='hospital_logos/', blank=True, null=True)
    
    # Blood Inventory / Stats
    storage_capacity = models.PositiveIntegerField(default=0)
    requests = models.TextField(blank=True, null=True)
    

    license_upload = models.FileField(upload_to='hospital_licenses/', blank=True, null=True)

    def __str__(self):
        return self.hospital_name
    
    
# ------------------ Blood Stock ------------------
class BloodStock(models.Model):
    units = models.PositiveIntegerField(default=0)
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, null=True, blank=True)
    blood_group = models.CharField(max_length=3, choices=[
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
    ])
    units_available = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.blood_group} ({self.units_available} units)"


# ------------------ Blood Request ------------------
class BloodRequest(models.Model):
    hospital = models.ForeignKey(HospitalProfile, on_delete=models.CASCADE, related_name="blood_requests")
    blood_group = models.CharField(
        max_length=3,
        choices=[
            ('A+', 'A+'), ('A-', 'A-'),
            ('B+', 'B+'), ('B-', 'B-'),
            ('O+', 'O+'), ('O-', 'O-'),
            ('AB+', 'AB+'), ('AB-', 'AB-'),
        ]
    )

    units_requested = models.PositiveIntegerField()
    date_required = models.DateField()

    #  New field for emergency
    is_emergency = models.BooleanField(default=False)

    request_date = models.DateTimeField(auto_now_add=True)
    status_choices = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=10, choices=status_choices, default='Pending')

    def __str__(self):
        return f"{self.status}"
    
class PatientBloodRequest(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    units_Requested = models.PositiveIntegerField()
    hospital_Name = models.CharField(max_length=40)
    date_Required = models.DateField()
    is_Emergency = models.BooleanField(default=False)
    request_date = models.DateTimeField(auto_now_add=True)
    status_choices = [('Pending','Pending'),('Approved','Approved'),('Rejected','Rejected')]
    status = models.CharField(max_length=10, choices=status_choices, default='Pending')

    
class BloodDonation(models.Model):
    donor = models.ForeignKey('DonorProfile', on_delete=models.CASCADE)
    patient = models.ForeignKey('PatientProfile', on_delete=models.CASCADE)
    hospital = models.ForeignKey('HospitalProfile', on_delete=models.CASCADE)
    blood_group = models.CharField(max_length=5)
    units = models.PositiveIntegerField(default=1)
    date_donated = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.donor.user.username} → {self.patient.user.username} ({self.blood_group})"
    
class BloodDonationCamp(models.Model):
    hospital = models.ForeignKey('HospitalProfile', on_delete=models.CASCADE)
    camp_name = models.CharField(max_length=100)
    date = models.DateField()
    venue = models.CharField(max_length=150)
    organizer = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.camp_name} ({self.hospital.hospital_name})"
    
# models.py
from django.contrib.auth.models import User

class Notification(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('donor', 'Donor'),
        ('hospital', 'Hospital'),
        ('patient', 'Patient'),
    ]

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # optional (for emergency style alert)
    type = models.CharField(max_length=20, default='info')  
    # e.g. 'info', 'warning', 'emergency', 'success'

    def __str__(self):
        return f"{self.role} - {self.title}"



class DonorAppointmentRequest(models.Model):
    donor = models.ForeignKey(User, on_delete=models.CASCADE)
    responses = models.JSONField()  # to store answers as JSON
    submitted_on = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending')
    remarks = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Request by {self.donor.username} on {self.submitted_on.date()}"