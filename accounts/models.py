from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class PrivacyConsent(models.Model):
    user = models.OneToOneField('accounts.User', on_delete=models.CASCADE, related_name='privacy_consent')
    accepted = models.BooleanField(default=False)
    accepted_at = models.DateTimeField(null=True, blank=True)
    version = models.CharField(max_length=20, default="1.0")  # for future updates
    location_granted = models.BooleanField(default=False)

    def __str__(self):
        return f"PrivacyConsent(user={self.user.username}, accepted={self.accepted})"


class User(AbstractUser):
    ROLE_CHOICES = [
        ('Empleado', 'EMPLOYEE'),
        ('HR_Admin', 'HR_ADMIN'),
        ('Master_Admin', 'MASTER_ADMIN'),
    ]
    SHIFT_CHOICES = [
        ('Fijo (8 Hrs)', 'FIXED_8HRS'),
        ('Mixto (8 Hrs)', 'MIXED_8HRS'),
        ('Mixto (12 Hrs)', 'MIXED_12HRS'),
    ]
    EMP_STATUS_CHOICES = [
        ('activo', 'active'),
        ('inactivo', 'terminated'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    employee_id = models.CharField(
        max_length=5,
        unique=True,
        validators=[MinLengthValidator(5)],
        help_text="Exactamente 5 digitos, agregar 0's (e.g. 00037)"
    )
    company = models.CharField(max_length=100, blank=True)

    active_as_of = models.DateTimeField(null=True, blank=True)
    employee_status = models.CharField(max_length=20, choices=EMP_STATUS_CHOICES, default='active')
    shift = models.CharField(max_length=20, choices=SHIFT_CHOICES, default='FIXED_8HRS')
    utilization = models.BooleanField(default=False)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    street_name = models.CharField(max_length=255, blank=True)
    address_number = models.CharField(max_length=50, blank=True)
    neighborhood = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    district = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['company']),
            models.Index(fields=['shift']),
            models.Index(fields=['is_active']),
            models.Index(fields=['employee_status']),
        ]

    def save(self, *args, **kwargs):
        if self.employee_id:
            self.employee_id = str(self.employee_id).zfill(5)[:5]
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def ensure_privacy_consent(sender, instance, created, **kwargs):
    if created:
        PrivacyConsent.objects.get_or_create(user=instance)