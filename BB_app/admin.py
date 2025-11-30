from django.contrib import admin

from .models import (
    Profile, HospitalProfile, DonorProfile, PatientProfile, Contact,
    BloodStock, BloodRequest, BloodDonation, BloodDonationCamp,
    DonorAppointmentRequest, Notification, PatientBloodRequest
)

# ------------------- Custom Admin for BloodRequest -------------------
@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ('hospital', 'blood_group', 'units_requested', 'date_required', 'status', 'request_date')

    # 🔥 Hide rejected requests from admin table
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(status="Rejected")


# ------------------- Custom Admin for PatientBloodRequest -------------------
@admin.register(PatientBloodRequest)
class PatientBloodRequestAdmin(admin.ModelAdmin):
    list_display = ('patient', 'units_Requested', 'hospital_Name', 'date_Required', 'status', 'request_date')

    # 🔥 Hide rejected requests from admin table
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(status="Rejected")


# Register remaining models normally
admin.site.register(Profile)
admin.site.register(DonorProfile)
admin.site.register(HospitalProfile)
admin.site.register(PatientProfile)
admin.site.register(Contact)
admin.site.register(BloodStock)
admin.site.register(BloodDonation)
admin.site.register(BloodDonationCamp)
admin.site.register(DonorAppointmentRequest)
admin.site.register(Notification)
