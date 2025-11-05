from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import BloodDonationCampForm, LoginForm, PatientBloodRequestForm, ResetPasswordForm, UserForm, ContactForm, DonorForm, PatientForm, HospitalForm,HospitalProfile,DonorProfile,PatientProfile
from .models import BloodDonationCamp, PatientBloodRequest, Profile
from django.contrib.auth.models import User
from .models import HospitalProfile, BloodStock, BloodRequest,BloodDonation,Notification
from .forms import BloodStockForm, BloodRequestForm
from .models import DonorAppointmentRequest
from .forms import DonorAppointmentRequestForm
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum
from django.db import models
from datetime import date
import io
import base64
from matplotlib import pyplot as plt

from django.db.models import Q

# --- Home Page ---
def home(request):
    return render(request, 'home.html')


# --- Help Page ---
def help(request):
    return render(request, 'help.html')


# --- Contact Page ---
def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thank you for contacting PulsePoint Blood Bank! We'll get back to you soon.")
            return redirect('contact')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})


# --- Register ---
def signup(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            # Save user
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # hash password
            user.save()

            # Save profile (role)
            role = request.POST.get('role')
            Profile.objects.create(user=user, role=role)

            return redirect('login')
    else:
        form = UserForm()

    return render(request, 'signup.html', {'form': form})


# --- Login ---
def login_View(request):
    # Fetch the first superuser (for demo display)
    admin_user = User.objects.filter(is_superuser=True).first()
    admin_username = admin_user.username if admin_user else "Not found"
    admin_password = "Muhsina123"

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)

                # Redirect based on role
                if user.is_superuser:
                    messages.success(request, "Welcome Admin!")
                    return redirect('admin_dashboard')

                role = user.profile.role

                if role == 'donor':
                    if DonorProfile.objects.filter(user=user).exists():
                        messages.info(request, "Welcome back!")
                        return redirect('donor_dashboard')
                    else:
                        return redirect('donor_form')

                elif role == 'patient':
                    if PatientProfile.objects.filter(user=user).exists():
                        messages.info(request, "Welcome back!")
                        return redirect('patient_dashboard')
                    else:
                        return redirect('patient_form')

                elif role == 'hospital':
                    if HospitalProfile.objects.filter(user=user).exists():
                        messages.info(request, "Welcome back!")
                        return redirect('hospital_dashboard')
                    else:
                        return redirect('hospital_form')

                else:
                    messages.warning(request, "Unknown role, redirecting to home.")
                    return redirect('home')

            else:
                return render(request, 'login.html', {
                    'form': form,
                    'error': 'Invalid credentials',
                    'admin_username': admin_username,
                    'admin_password': admin_password
                })
    else:
        form = LoginForm()

    return render(request, 'login.html', {
        'form': form,
        'admin_username': admin_username,
        'admin_password': admin_password
    })


# --- Forgot Password from login page ---
def forgot_password(request):
    if request.method == 'POST':
        username = request.POST.get('username').strip()

        if not username:
            return render(request, 'login.html', {
                'form': LoginForm(),
                'error': 'Please enter your username first.'
            })

        try:
            user = User.objects.get(username=username)
            # Username found → redirect to reset password page
            return redirect('reset_password', user_id=user.id)

        except User.DoesNotExist:
            # Username invalid → show error *without redirecting*
            form = LoginForm(initial={'username': username})
            return render(request, 'login.html', {
                'form': form,
                'error': 'User not found. Please enter a valid username.'
            })


# --- Reset Password ---

def reset_password(request, user_id):
    user = get_object_or_404(User, id=user_id)
    success_message = None  # message flag

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            user.set_password(new_password)
            user.save()
            # Show success message in same page instead of redirect
            success_message = "Password reset successfully! Redirecting to login..."
    else:
        form = ResetPasswordForm()

    return render(request, 'reset_password.html', {
        'form': form,
        'success_message': success_message
    })
    
    


# 🏥 Dashboard Home
@login_required
def hospital_dashboard(request):
    hospital = get_object_or_404(HospitalProfile, user=request.user)
    today = date.today()

    upcoming_camps = BloodDonationCamp.objects.filter(hospital=hospital, date__gte=today)
    for camp in upcoming_camps:
        days_left = (camp.date - today).days
        if 0 < days_left <= 2:
            already_notified_today = Notification.objects.filter(
                recipient=request.user,
                title="Upcoming Blood Donation Camp",
                message__icontains=camp.camp_name,
                created_at__date=date.today()
            ).exists()

            if not already_notified_today:
                Notification.objects.create(
                    recipient=request.user,
                    title="Upcoming Blood Donation Camp",
                    message=f"Your camp '{camp.camp_name}' is scheduled for {camp.date}. Please prepare accordingly.",
                    role="hospital",
                )

    # Latest notifications
    notifications = Notification.objects.filter(
        Q(role='hospital') | Q(recipient=request.user)
    ).order_by('-created_at')[:5]

    # Count unread
    unread_count = Notification.objects.filter(
        Q(role='hospital') | Q(recipient=request.user),
        is_read=False
    ).count()

    return render(request, 'hospital_dashboard.html', {
        'hospital': hospital,
        'notifications': notifications,
        'unread_count': unread_count,
    })




# 📊 Stock (Pie Chart)
@login_required
def hospital_stock(request, id=None):
    # If admin is viewing a specific hospital’s stock
    if request.user.is_superuser and id:
        hospital = get_object_or_404(HospitalProfile, id=id)
        is_admin_view = True
    else:
        # Hospital user viewing their own stock
        hospital = get_object_or_404(HospitalProfile, user=request.user)
        is_admin_view = False

    blood_stocks = BloodStock.objects.filter(hospital=hospital)

    # Combine duplicates by blood group
    stock_summary = {}
    for stock in blood_stocks:
        stock_summary[stock.blood_group] = stock_summary.get(stock.blood_group, 0) + stock.units_available

    # Prepare chart data
    labels = list(stock_summary.keys())
    values = list(stock_summary.values())

    # --- Generate Pie Chart using Matplotlib ---
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
    ax.set_title('Blood Stock Distribution')

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    chart_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close(fig)

    return render(request, 'hospital_stock.html', {
        'hospital': hospital,
        'blood_stocks': blood_stocks,
        'chart_image': chart_image,
        'is_admin_view': is_admin_view  # this flag controls the back button
    })

# ➕ Add Stock
@login_required
def add_stock(request):
    is_admin = request.user.is_superuser
    hospital = None

    if not is_admin:
        hospital = get_object_or_404(HospitalProfile, user=request.user)

    if request.method == 'POST':
        form = BloodStockForm(request.POST)
        if form.is_valid():
            blood_group = form.cleaned_data['blood_group']
            units = form.cleaned_data['units_available']

            if is_admin:
                stock, created = BloodStock.objects.get_or_create(
                    hospital=None,
                    blood_group=blood_group,
                    defaults={'units_available': 0}
                )
                stock.units_available += units
                stock.save()
                messages.success(request, f"{units} units added to admin stock for {blood_group}.")
                return redirect('manage_stock')
            else:
                existing_stock = BloodStock.objects.filter(hospital=hospital, blood_group=blood_group).first()
                if existing_stock:
                    existing_stock.units_available += units
                    existing_stock.save()
                    messages.success(request, f"{units} units added to existing stock of {blood_group}.")
                else:
                    new_stock = form.save(commit=False)
                    new_stock.hospital = hospital
                    new_stock.save()
                    messages.success(request, f"New blood group {blood_group} added with {units} units.")

              # 🩸 Create one shared notification for all patients
            title = "🩸 New Blood Stock Added"
            message = f"{hospital.hospital_name} added {units} units of {blood_group} to their stock."
            exists = Notification.objects.filter(
            title=title,
            message=message,
            role='patient'
            ).exists()
            if not exists:
                Notification.objects.create(
                    role='patient',
                    title=title,
                    message=message,
                   type='info'
                   )
                return redirect('hospital_stock', id=hospital.id)
    else:
        form = BloodStockForm()

    cancel_url = 'manage_stock' if is_admin else 'hospital_dashboard'
    return render(request, 'add_stock.html', {'form': form, 'cancel_url': cancel_url})


# 🩸 Request Blood
@login_required
def request_blood(request):
    hospital = get_object_or_404(HospitalProfile, user=request.user)

    if request.method == 'POST':
        form = BloodRequestForm(request.POST)
        if form.is_valid():
            blood_request = form.save(commit=False)
            blood_request.hospital = hospital  # assign current hospital
            blood_request.save()
            messages.success(request, "Blood request submitted successfully.")
            return redirect('hospital_dashboard')
    else:
        form = BloodRequestForm()

    return render(request, 'request_blood.html', {'form': form})


@login_required
def patient_blood_request(request):
    patient = request.user.patientprofile
    if request.method == 'POST':
        form = PatientBloodRequestForm(request.POST)
        if form.is_valid():
            blood_request = form.save(commit=False)
            blood_request.patient = patient
            blood_request.save()
            messages.success(request, "Your blood request has been submitted successfully.")
            return redirect('patient_dashboard')
    else:
        form = PatientBloodRequestForm()
    return render(request, 'patient_blood_request.html', {'form': form})



# 📋 View Requests
@login_required
def view_request(request):
    hospital = get_object_or_404(HospitalProfile, user=request.user)
    requests = BloodRequest.objects.filter(hospital=hospital).order_by('-request_date')
    return render(request, 'view_request.html', {'requests': requests})


# 👤 Profile View / Update / Delete
@login_required
def hospital_profile_view(request):
    hospital = get_object_or_404(HospitalProfile, user=request.user)

    if request.method == 'POST':
        form = HospitalForm(request.POST, request.FILES, instance=hospital)
        if form.is_valid():
            # If license_upload not included, old one remains unchanged
            form.save(commit=False)
            form.instance.license_upload = hospital.license_upload  # preserve old file
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('hospital_dashboard')
    else:
        form = HospitalForm(instance=hospital)

        # 👇 Optionally remove the field dynamically before rendering
        if 'license_upload' in form.fields:
            del form.fields['license_upload']

    return render(request, 'hospital_profile.html', {'form': form})



@login_required
def hospital_profile_delete(request):
    hospital = get_object_or_404(HospitalProfile, user=request.user)
    user = hospital.user
    hospital.delete()
    user.delete()
    messages.info(request, "Your profile has been deleted.")
    return redirect('login')

@login_required
def update_camp(request, id):
    camp = get_object_or_404(BloodDonationCamp, id=id)
    if request.method == 'POST':
        form = BloodDonationCampForm(request.POST, instance=camp)
        if form.is_valid():
            form.save()
            return redirect('blood_camp')
    else:
        form = BloodDonationCampForm(instance=camp)
    return render(request, 'update_camp.html', {'form': form})

@login_required
def delete_camp(request, id):
    camp = get_object_or_404(BloodDonationCamp, id=id)
    camp.delete()
    return redirect('blood_camp')

@login_required
def donor_dashboard(request):
    donor = DonorProfile.objects.get(user=request.user)
    notifications = Notification.objects.filter(role='donor').order_by('-created_at')[:5]
    return render(request, 'donor_dashboard.html', {'donor': donor, 'notifications': notifications})


@login_required
def donor_profile(request):
    donor = get_object_or_404(DonorProfile, user=request.user)  # Fetch donor profile

    if request.method == 'POST':
        form = DonorForm(request.POST, request.FILES, instance=donor)
        if form.is_valid():
            # If profile picture not included, old one remains unchanged
            form.save(commit=False)
            form.instance.profile_pic = donor.profile_pic  # preserve old profile picture
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('donor_dashboard')  # Redirect to the donor dashboard after update
    else:
        form = DonorForm(instance=donor)  # Prepopulate the form with donor data

    return render(request, 'donor_profile.html', {'form': form, 'donor': donor})


@login_required
def donor_profile_delete(request, donor_id):
    donor = get_object_or_404(DonorProfile, id=donor_id)

    if request.method == 'POST':
        donor.delete()
        return redirect('donor_dashboard') 

    return render(request, 'confirm_delete.html', {'donor': donor})

@login_required
def donor_appoinment(request):
    if request.method == 'POST':
        form = DonorAppointmentRequestForm(request.POST)
        if form.is_valid():
            # Save all answers into the database
            responses = form.cleaned_data
            DonorAppointmentRequest.objects.create(
                donor=request.user,
                responses=responses,
                status='Pending'
            )
            messages.success(request, "Your donation appointment request has been submitted successfully!")
            return redirect('donor_dashboard')
    else:
        form = DonorAppointmentRequestForm()

    return render(request, 'donor_appoinment.html', {'form': form})

@login_required
def donation_status(request):
    donor_requests = DonorAppointmentRequest.objects.filter(donor=request.user).order_by('-submitted_on')
    return render(request, 'donation_status.html', {'donor_requests': donor_requests})



# ---------- 1. Donation History ----------
def donation_history(request):
    donor = request.user
    donations = DonorAppointmentRequest.objects.filter(donor=donor).order_by('-submitted_on')
    return render(request, 'donation_history.html', {'donations': donations})


# ---------- 2. Camps ----------
def donor_camp(request):
    camps = BloodDonationCamp.objects.all().order_by('-date')
    return render(request, 'donor_camp.html', {'camps': camps})


# ---------- 3. Hospitals ----------
def view_hospital(request):
    hospitals = HospitalProfile.objects.all().order_by('hospital_name')
    return render(request, 'view_hospital.html', {'hospitals': hospitals})



# --- Logout ---
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def patient_form(request):
    if PatientProfile.objects.filter(user=request.user).exists():
        return redirect('patient_dashboard')

    if request.method == 'POST':
        form = PatientForm(request.POST, request.FILES)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.user = request.user
            patient.save()
            messages.success(request, "Patient details submitted successfully!")
            return redirect('patient_dashboard')
    else:
        form = PatientForm()
    return render(request, 'patient_form.html', {'form': form})



@login_required
def donor_form(request):
    # Redirect if already filled
    if DonorProfile.objects.filter(user=request.user).exists():
        return redirect('donor_dashboard')

    # Form submission logic
    if request.method == 'POST':
        form = DonorForm(request.POST, request.FILES)
        if form.is_valid():
            donor = form.save(commit=False)
            donor.user = request.user
            donor.save()
            messages.success(request, "Donor details submitted successfully!")
            return redirect('donor_dashboard')
    else:
        form = DonorForm()

    return render(request, 'donor_form.html', {'form': form})



@login_required
def hospital_form(request):
    if HospitalProfile.objects.filter(user=request.user).exists():
        return redirect('hospital_dashboard')

    if request.method == 'POST':
        form = HospitalForm(request.POST, request.FILES)
        if form.is_valid():
            hospital = form.save(commit=False)
            hospital.user = request.user
            hospital.save()
            messages.success(request, "Hospital details submitted successfully!")
            return redirect('hospital_dashboard')
    else:
        form = HospitalForm()
    
    return render(request, 'hospital_form.html', {'form': form})



@login_required
def blood_camp(request):
    hospital = get_object_or_404(HospitalProfile, user=request.user)
    camps = BloodDonationCamp.objects.filter(hospital=hospital).order_by('-date')
    return render(request, 'blood_camp.html', {'camps': camps})

@login_required
def create_camp(request):
    hospital = get_object_or_404(HospitalProfile, user=request.user)
    if request.method == 'POST':
        form = BloodDonationCampForm(request.POST)
        if form.is_valid():
            camp = form.save(commit=False)
            camp.hospital = hospital
            camp.save()
            messages.success(request, "Blood donation camp created successfully!")
            Notification.objects.create(
                role='admin',
                title="🩸 New Blood Donation Camp",
                message=f"{hospital.hospital_name} scheduled '{camp.camp_name}' on {camp.date} at {camp.venue}."
                )
            Notification.objects.create(
                role='donor',
                title="🩸 New Donation Camp!",
                message=f"Join the camp '{camp.camp_name}' on {camp.date} at {camp.venue} organized by {hospital.hospital_name}."
                )
            Notification.objects.create(
                role='patient',
                title="❤️ Blood Donation Camp Announced",
                message=f"{hospital.hospital_name} is organizing '{camp.camp_name}' on {camp.date} at {camp.venue}. You can inform donors or visit for support!"
)

            return redirect('blood_camp')
    else:
        form = BloodDonationCampForm()
    return render(request, 'create_camp.html', {'form': form})

@login_required
def mark_notification_read(request, notification_id):
    notif = get_object_or_404(Notification, id=notification_id)
    notif.is_read = True
    notif.save()
    return redirect('hospital_dashboard')


@login_required
def generate_report(request):
    donations = BloodDonation.objects.select_related('donor', 'patient').all()

    return render(request, 'generate_report.html', {'donations': donations})


@login_required
def patient_dashboard(request):
    patient = request.user.patientprofile

    # Unread notifications count
    unread_count = Notification.objects.filter(
        Q(recipient=request.user) | Q(role='patient'),
        is_read=False
    ).count()

    context = {
        'patient': patient,
        'unread_count': unread_count,
    }
    return render(request, 'patient_dashboard.html', context)


@login_required
def search_blood(request):
    query = request.GET.get('hospital', '')

    location = request.GET.get('location', '')
    blood_group = request.GET.get('blood_group', '')
    blood_groups = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]


    # Start with all blood stocks joined with hospital
    blood_stocks = BloodStock.objects.select_related('hospital').exclude(hospital__isnull=True)


    # Filter by blood group
    if blood_group:
        blood_stocks = blood_stocks.filter(blood_group=blood_group)

    # Filter by location
    if location:
        blood_stocks = blood_stocks.filter(hospital__location__icontains=location)

    # Filter by hospital name (if 'q' used as hospital search)
    if query:
        blood_stocks = blood_stocks.filter(hospital__hospital_name__icontains=query)

    # 🩸 Combine duplicates: same hospital + same blood group → sum units
    blood_stocks = (
        blood_stocks
        .values(
            'hospital__hospital_name',
            'hospital__location',
            'blood_group'
        )
        .annotate(total_units=Sum('units_available'))
        .order_by('hospital__hospital_name', 'blood_group')
    )

    context = {
        'blood_stocks': blood_stocks,
        'query': query,
        'location': location,
        'blood_group': blood_group,
        'blood_groups': blood_groups,
    }

    return render(request, 'search_blood.html', context)

@login_required
def track_request(request):
    patient = request.user.patientprofile
    blood_requests = PatientBloodRequest.objects.filter(patient=patient).order_by('-request_date')
    return render(request, 'track_request.html', {'blood_requests': blood_requests})

# Edit Patient Blood Request
@login_required
def edit_patient_request(request, request_id):
    blood_request = get_object_or_404(PatientBloodRequest, id=request_id, patient=request.user.patientprofile)
    
    # Only allow editing if status is Pending
    if blood_request.status != 'Pending':
        messages.warning(request, "You can only edit requests that are pending.")
        return redirect('track_request')
    
    if request.method == 'POST':
        form = PatientBloodRequestForm(request.POST, instance=blood_request)
        if form.is_valid():
            form.save()
            messages.success(request, "Blood request updated successfully.")
            return redirect('track_request')
    else:
        form = PatientBloodRequestForm(instance=blood_request)
    
    return render(request, 'edit_patient_request.html', {'form': form})


# Delete Patient Blood Request
@login_required
def delete_patient_request(request, request_id):
    blood_request = get_object_or_404(PatientBloodRequest, id=request_id, patient=request.user.patientprofile)
    
    if blood_request.status != 'Pending':
        messages.warning(request, "You can only delete requests that are pending.")
        return redirect('patient_dashboard')
    
    if request.method == 'POST':
        blood_request.delete()
        messages.success(request, "Blood request deleted successfully.")
        return redirect('patient_dashboard')
    
    return redirect('patient_dashboard')



@login_required
def received_history(request):
    patient = get_object_or_404(PatientProfile, user=request.user)
    received = BloodDonation.objects.filter(patient=patient).order_by('-date_donated')
    return render(request, 'received_history.html', {'received': received})

@login_required
def patient_profile(request):
    patient = get_object_or_404(PatientProfile, user=request.user)

    if request.method == 'POST':
        patientform = PatientForm(request.POST, request.FILES, instance=patient)
        if patientform.is_valid():
            patientform.save()
            messages.success(request, 'Your profile has been updated successfully!')
            return redirect('patient_dashboard')
    else:
        patientform = PatientForm(instance=patient)

    return render(request, 'patient_profile.html', {'patientform': patientform, 'patient': patient})

@login_required
def patient_profile_delete(request, id):
    patient = get_object_or_404(PatientProfile, id=id)
    patient.delete()
    messages.warning(request, 'Your profile has been deleted.')
    return redirect('login') 


from django.contrib.auth.decorators import user_passes_test
from django.db.models import Sum

# ✅ Restrict access to superusers only
def admin_required(view_func):
    return user_passes_test(lambda u: u.is_superuser, login_url='login')(view_func)

from .models import Notification

@admin_required
def admin_dashboard(request):
    total_donors = DonorProfile.objects.count()
    total_hospitals = HospitalProfile.objects.count()
    total_requests = BloodRequest.objects.count()
    total_stock_units = BloodStock.objects.aggregate(total=Sum('units_available'))['total'] or 0

    # Count unread notifications for admin
    notification_count = Notification.objects.filter(role='admin', is_read=False).count()

    return render(request, 'admin_dashboard.html', {
        'total_donors': total_donors,
        'total_hospitals': total_hospitals,
        'total_requests': total_requests,
        'total_stock_units': total_stock_units,
        'notification_count': notification_count,
    })



@admin_required
def view_users(request):
    hospitals = HospitalProfile.objects.all()
    donors = DonorProfile.objects.all()
    patients = PatientProfile.objects.all()

    return render(request, 'view_users.html', {
        'hospitals': hospitals,
        'donors': donors,
        'patients': patients
    })

@admin_required
def manage_stock_admin(request):
    stocks = BloodStock.objects.select_related('hospital').all().order_by('hospital__hospital_name')
    return render(request, 'manage_stock.html', {'stocks': stocks})

@admin_required
def admin_hospital_stock(request):
    hospitals = HospitalProfile.objects.all()
    return render(request, 'admin_hospital_stock.html', {'hospitals': hospitals})

@admin_required
def view_reports(request):
    donations = BloodDonation.objects.select_related('donor', 'patient', 'hospital').all()
    return render(request, 'view_reports.html', {'donations': donations})

@login_required
def manage_stock(request):
    stocks = BloodStock.objects.filter(hospital__isnull=True)
    return render(request, 'manage_stock.html', {'stocks': stocks})

@login_required
def notifications(request):
    user = request.user

    # Determine role
    user_role = user.profile.role if hasattr(user, 'profile') else 'admin'

    # Get all notifications for this user or their role
    notifications = Notification.objects.filter(
        Q(recipient=user) | Q(role=user_role)
    ).order_by('-created_at')

    # Mark unread ones as read
    Notification.objects.filter(
        Q(recipient=user) | Q(role=user_role), is_read=False
    ).update(is_read=True)

    return render(request, 'notifications.html', {'notifications': notifications})

@login_required
def manage_request(request):
    request_type = request.GET.get('type', None)  # hospital / patient / donor

    hospital_requests = BloodRequest.objects.filter(status='Pending')
    patient_requests = PatientProfile.objects.all()  # adjust if patients send blood request
    donor_requests = DonorAppointmentRequest.objects.filter(status='Pending')

    # Default context (only show cards)
    context = {
        'show_table': False,
        'hospital_count': hospital_requests.count(),
        'patient_count': patient_requests.count(),
        'donor_count': donor_requests.count(),
    }

    # If user clicked a card
    if request_type == 'hospital':
        context.update({
            'show_table': True,
            'table_title': "Hospital Requests",
            'requests': hospital_requests,
            'type': 'hospital',
        })
    elif request_type == 'donor':
        context.update({
            'show_table': True,
            'table_title': "Donor Requests",
            'requests': donor_requests,
            'type': 'donor',
        })
    elif request_type == 'patient':
        context.update({
            'show_table': True,
            'table_title': "Patient Requests",
            'requests': patient_requests,
            'type': 'patient',
        })

    return render(request, 'manage_requests.html', context)


@login_required
def approve_request(request, id):
    blood_request = get_object_or_404(BloodRequest, id=id)
    blood_request.status = 'Approved'
    blood_request.save()

    # ✅ Notify Hospital
    Notification.objects.create(
        recipient=blood_request.hospital.user,
        role='hospital',
        title="Blood Request Approved",
        message=f"Your blood request for {blood_request.patient_name} ({blood_request.blood_group}) has been approved by Admin."
    )

    # ✅ Notify Patient
    patient = PatientProfile.objects.filter(full_name=blood_request.patient_name).first()
    if patient:
        Notification.objects.create(
            recipient=patient.user,
            role='patient',
            title="🎉 Blood Request Approved",
            message=f"Good news! Your blood request for {blood_request.blood_group} has been approved."
        )

    messages.success(request, "Blood request approved successfully.")
    return redirect('manage_request')


@login_required
def reject_request(request, id):
    blood_request = get_object_or_404(BloodRequest, id=id)
    patient_name = blood_request.patient_name
    blood_group = blood_request.blood_group
    hospital_user = blood_request.hospital.user
    blood_request.delete()

    # ✅ Notify Hospital
    Notification.objects.create(
        recipien=blood_request.hospital.user,
        role='hospital',
        title="Blood Request Rejected",
        message=f"Your blood request for {patient_name} ({blood_group}) has been rejected by Admin."
    )

    # ✅ Notify Patient
    patient = PatientProfile.objects.filter(full_name=patient_name).first()
    if patient:
        Notification.objects.create(
            recipient=patient.user,
            role='patient',
            title="❌ Blood Request Rejected",
            message=f"Sorry! Your blood request for {blood_group} was rejected by Admin."
        )

    messages.warning(request, "Blood request rejected and deleted successfully.")
    return redirect('manage_request')

@login_required
def delete_camp(request, camp_id):
    camp = get_object_or_404(BloodDonationCamp, id=camp_id, hospital__user=request.user)
    hospital = camp.hospital

    # 🩸 Store camp name before deleting it
    camp_name = camp.camp_name

    # 🧹 Delete any existing "upcoming camp" notifications related to this camp
    Notification.objects.filter(
        title="Upcoming Blood Donation Camp",
        message__icontains=camp_name
    ).delete()

    # 🧨 Notify patients about the cancellation (avoid duplicates)
    title = "🚨 Blood Donation Camp Cancelled"
    message = f"{hospital.hospital_name} has cancelled the blood donation camp '{camp_name}'."

    exists = Notification.objects.filter(
        title=title,
        message=message,
        role='patient'
    ).exists()

    if not exists:
        Notification.objects.create(
            role='patient',
            title=title,
            message=message,
            type='emergency'  # 🔴 appears in red (emergency style)
        )

    # ❌ Delete the camp
    camp.delete()

    messages.success(request, f"Camp '{camp_name}' was deleted and patients have been notified.")
    return redirect('hospital_dashboard')
