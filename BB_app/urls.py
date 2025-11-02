from . import views
from django.urls import path

urlpatterns = [
    path('',views.home,name='home'),
    path('login/',views.login_View,name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('help&support/',views.help,name='help'),
    path('contact/',views.contact_view,name='contact'),
    
    
    path('patient_form/',views.patient_form,name='patient_form'),
    path('donor_form/',views.donor_form,name='donor_form'),
    path('hospital_form/',views.hospital_form,name='hospital_form'),
    
   
    path('hospital_dashboard/', views.hospital_dashboard, name='hospital_dashboard'),
    path('hospital_dashboard/stock/<int:id>/', views.hospital_stock, name='hospital_stock'),
    path('add_stock/', views.add_stock, name='add_stock'),
    path('hospital_dashboard/request_blood/', views.request_blood, name='request_blood'),
    path('hospital_dashboard/view_request/', views.view_request, name='view_request'),
    path('hospital_dashboard/profile/', views.hospital_profile_view, name='hospital_profile_view'),
    path('hospital_dashboard/delete_profile/', views.hospital_profile_delete, name='hospital_profile_delete'),
    path('blood_camp/', views.blood_camp, name='blood_camp'),
    path('generate_report/', views.generate_report, name='generate_report'),
    path('create_camp/', views.create_camp, name='create_camp'),
    path('camp/update/<int:id>/', views.update_camp, name='update_camp'),
    path('camp/delete/<int:id>/', views.delete_camp, name='delete_camp'),
    path('mark_notification/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    
    
    path('patient_dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('patient/search_blood/', views.search_blood, name='search_blood'),
    path('patient/request_blood/', views.patient_blood_request, name='patient_blood_request'),
    path('patient/track_request/', views.track_request, name='track_request'),
    path('patient/received_history/', views.received_history, name='received_history'),
    path('patient/profile/', views.patient_profile, name='patient_profile'),
    path('patient/profile/delete/<int:id>/', views.patient_profile_delete, name='patient_profile_delete'),


    path('view/hospital/', views.view_hospital, name='view_hospital'),
    
    
    path('donor_dashboard/',views.donor_dashboard,name='donor_dashboard'),
    path('donor/profile/', views.donor_profile, name='donor_profile'),
    path('donor/<int:donor_id>/profile/delete/', views.donor_profile_delete, name='donor_profile_delete'),
    path('donor/appoinment/', views.donor_appoinment, name='donor_appoinment'),
    path('donor/donation_status/', views.donation_status, name='donation_status'),
    path('donor/donation_history/', views.donation_history, name='donation_history'),
    path('donor/camp/', views.donor_camp, name='donor_camp'),
    path('donor/notifications/', views.donor_notifications, name='donor_notifications'),
    
    
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('view_users/', views.view_users, name='view_users'),
    path('manage_stock/', views.manage_stock, name='manage_stock'),
    path('admin_hospital_stock/', views.admin_hospital_stock, name='admin_hospital_stock'),
    path('view_reports/', views.view_reports, name='view_reports'),

    
        # --- Password Reset ---
    path('forgot_password/', views.forgot_password, name='forgot_password'),
    path('reset_password/<int:user_id>/', views.reset_password, name='reset_password'),
]
