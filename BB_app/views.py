from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import BloodDonationCampForm, LoginForm, ResetPasswordForm, UserForm, ContactForm, DonorForm, PatientForm, HospitalForm,HospitalProfile,DonorProfile,PatientProfile
from .models import BloodDonationCamp, Profile
from django.contrib.auth.models import User
from .models import HospitalProfile, BloodStock, BloodRequest,BloodDonation,Notification
from .forms import BloodStockForm, BloodRequestForm
from .models import DonorAppointmentRequest
from .forms import DonorAppointmentRequestForm
import io
import base64
from matplotlib import pyplot as plt

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
    notifications = Notification.objects.filter(hospital=hospital).order_by('-created_at')[:5]
    return render(request, 'hospital_dashboard.html', {
        'hospital': hospital,
        'notifications': notifications
    })



# 📊 Stock (Pie Chart)
@login_required
def hospital_stock(request):
    hospital = get_object_or_404(HospitalProfile, user=request.user)
    blood_stocks = BloodStock.objects.filter(hospital=hospital)

    # 🔹 Combine duplicates by blood group
    stock_summary = {}
    for stock in blood_stocks:
        if stock.blood_group in stock_summary:
            stock_summary[stock.blood_group] += stock.units_available
        else:
            stock_summary[stock.blood_group] = stock.units_available

    # Prepare data for chart
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
        'chart_image': chart_image
    })


# ➕ Add Stock
@login_required
def add_stock(request):
    hospital = get_object_or_404(HospitalProfile, user=request.user)

    if request.method == 'POST':
        form = BloodStockForm(request.POST)
        if form.is_valid():
            blood_group = form.cleaned_data['blood_group']
            units = form.cleaned_data['units_available']

            #  Check if this blood group already exists for the hospital
            existing_stock = BloodStock.objects.filter(hospital=hospital, blood_group=blood_group).first()

            if existing_stock:
                #  Update existing stock
                existing_stock.units_available += units
                existing_stock.save()
                messages.success(request, f"{units} units added to existing stock of {blood_group}.")
            else:
                #  Create new stock record
                new_stock = form.save(commit=False)
                new_stock.hospital = hospital
                new_stock.save()
                messages.success(request, f"New blood group {blood_group} added with {units} units.")

            return redirect('hospital_stock')

    else:
        form = BloodStockForm()

    return render(request, 'add_stock.html', {'form': form})



# 🩸 Request Blood
@login_required
def request_blood(request):
    hospital = get_object_or_404(HospitalProfile, user=request.user)

    if request.method == 'POST':
        form = BloodRequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.hospital = hospital
            req.save()

            # ✅ Emergency check
            if req.is_emergency:
                Notification.objects.create(
                    hospital=hospital,
                    title="🚨 Emergency Blood Request!",
                    message=f"⚠️ EMERGENCY: {req.patient_name} needs {req.units_requested} units of {req.blood_group} urgently!",
                )
            else:
                Notification.objects.create(
                    hospital=hospital,
                    title="Blood Request Submitted",
                    message=f"You have requested {req.units_requested} units of {req.blood_group} for patient {req.patient_name}.",
                )

            messages.success(request, "Blood request submitted successfully!")
            return redirect('hospital_dashboard')

    else:
        form = BloodRequestForm()

    return render(request, 'request_blood.html', {'form': form})
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


def patient_dashboard(request):
    return render(request,'patient_dashboard.html')

@login_required
def donor_dashboard(request):
    donor = DonorProfile.objects.get(user=request.user)
    return render(request, 'donor_dashboard.html', {'donor': donor})

@login_required
def donor_profile(request):
    donor = DonorProfile.objects.get(user=request.user)
    return render(request, 'donor_profile.html', {'donor': donor})



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


# ---------- 4. Notifications ----------
def donor_notifications(request):
    # Assuming you have a Notification model with fields title, message, and type
    notifications = Notification.objects.all().order_by('-id')
    return render(request, 'donor_notifications.html', {'notifications': notifications})


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
def admin_dashboard(request):
    return render(request,'admin_dashboard.html')

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
                hospital=hospital,
                title="New Blood Donation Camp Created",
                message=f"The camp '{camp.camp_name}' has been scheduled on {camp.date} at {camp.venue}."
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