from django.contrib import admin

from .models import Profile,HospitalProfile,DonorProfile,PatientProfile,Contact,BloodStock,BloodRequest,BloodDonation,BloodDonationCamp,DonorAppointmentRequest,Notification,PatientBloodRequest

# Register your models here.

admin.site.register(Profile),
admin.site.register(DonorProfile),
admin.site.register(HospitalProfile),
admin.site.register(PatientProfile),
admin.site.register(Contact),
admin.site.register(BloodStock),
admin.site.register(BloodRequest),
admin.site.register(BloodDonation),
admin.site.register(BloodDonationCamp),
admin.site.register(DonorAppointmentRequest),
admin.site.register(Notification),
admin.site.register(PatientBloodRequest),


