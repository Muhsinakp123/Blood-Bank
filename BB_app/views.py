from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import BloodDonationCampForm, LoginForm, ResetPasswordForm, UserForm, ContactForm, DonorForm, PatientForm, HospitalForm,HospitalProfile,DonorProfile,PatientProfile
from .models import BloodDonationCamp, Profile
from django.contrib.auth.models import User
from .models import HospitalProfile, BloodStock, BloodRequest,BloodDonation,Notification
from .forms import BloodStockForm, BloodRequestForm

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

    labels = [stock.blood_group for stock in blood_stocks]
    values = [stock.units_available for stock in blood_stocks]

    return render(request, 'hospital_stock.html', {
        'hospital': hospital,
        'labels': labels,
        'values': values,
        'blood_stocks': blood_stocks
    })


# ➕ Add Stock
@login_required
def add_stock(request):
    hospital = get_object_or_404(HospitalProfile, user=request.user)
    if request.method == 'POST':
        form = BloodStockForm(request.POST)
        if form.is_valid():
            stock = form.save(commit=False)
            stock.hospital = hospital
            stock.save()
            messages.success(request, f"Blood group {stock.blood_group} added successfully!")
            return redirect('hospital_dashboard')
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

    # ✅ Create notification
    Notification.objects.create(
        hospital=hospital,
        title="Blood Request Submitted",
        message=f"You have requested {req.units_requested} units of {req.blood_group} blood for patient {req.patient_name}.",
    )

    messages.success(request, "Blood request submitted successfully!")
    return redirect('hospital_dashboard')



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
        hospital.hospital_name = request.POST.get('hospital_name')
        hospital.location = request.POST.get('location')
        hospital.contact = request.POST.get('contact')
        hospital.email = request.POST.get('email')
        hospital.save()
        messages.success(request, "Profile updated successfully!")
    return render(request, 'hospital_profile.html', {'hospital': hospital})


@login_required
def hospital_profile_delete(request):
    hospital = get_object_or_404(HospitalProfile, user=request.user)
    user = hospital.user
    hospital.delete()
    user.delete()
    messages.info(request, "Your profile has been deleted.")
    return redirect('login')





def patient_dashboard(request):
    return render(request,'patient_dashboard.html')

def donor_dashboard(request):
    return render(request,'donor_dashboard.html')


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