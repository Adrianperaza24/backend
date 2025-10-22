from rest_framework.permissions import BasePermission

class IsHRorMaster(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        if not u or not u.is_authenticated:
            return False
        return u.is_superuser or u.groups.filter(name__in=['hr_admin', 'master_admin']).exists()