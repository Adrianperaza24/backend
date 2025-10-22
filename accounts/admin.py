from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, PrivacyConsent

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('id', 'username', 'employee_id', 'role', 'company', 'shift', 'is_active', 'employee_status', 'utilization', 'created_at')
    list_filter = ('role', 'company', 'shift', 'is_active', 'employee_status', 'utilization')
    search_fields = ('username', 'email', 'employee_id', 'company')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email',)}),
        ('HR', {'fields': ('role', 'employee_id', 'company', 'shift', 'utilization', 'employee_status', 'active_as_of')}),
        ('Location', {'fields': ('latitude', 'longitude', 'street_name', 'address_number', 'neighborhood', 'postal_code', 'district', 'state', 'country')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    def save_model(self, request, obj, form, change):
        password = form.cleaned_data.get('password')
        if password and not password.startswith('pbkdf2_'):
            obj.set_password(password)
        super().save_model(request, obj, form, change)

@admin.register(PrivacyConsent)
class PrivacyConsentAdmin(admin.ModelAdmin):
    list_display = ('user', 'accepted', 'accepted_at', 'version', 'location_granted')
    search_fields = ('user__username', 'user__employee_id', 'version')