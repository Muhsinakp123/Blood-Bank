from django.contrib import admin

from .models import Profile,HospitalProfile,DonorProfile,PatientProfile,Contact

# Register your models here.

admin.site.register(Profile),
admin.site.register(DonorProfile),
admin.site.register(HospitalProfile),
admin.site.register(PatientProfile),
admin.site.register(Contact),

