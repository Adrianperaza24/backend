from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from accounts.views import MeView, RegisterView, ProtectedView, PrivacyConsentView
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet, BusStopViewSet, CoverageMeshViewSet, RoutePlanViewSet,
    EmployeeLocationView, NearestStopView, NearbyStopsView, EmployeeRoutesView,
    # HR/Admin Data Management endpoints:
    hr_upload_active_employees, hr_upload_minimal_employees,
    hr_delete_employees, hr_upload_bus_stops, hr_delete_bus_stops,
    hr_delete_coverage_mesh, hr_upload_coverage_mesh, hr_upload_route_gpx, hr_delete_route,
    health
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'bus-stops', BusStopViewSet, basename='bus-stops')
router.register(r'coverage-meshes', CoverageMeshViewSet, basename='coverage-meshes')
router.register(r'route-plans', RoutePlanViewSet, basename='route-plans')


urlpatterns = [
    path("me/", MeView.as_view(), name="me"),
    path("register/", RegisterView.as_view(), name="register"),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('protected-view/', ProtectedView.as_view(), name="protected_view"),
    path("privacy-consent/", PrivacyConsentView.as_view(), name="privacy-consent"),

    # Map APIs
    path('map/employee/location/', EmployeeLocationView.as_view(), name='employee-location'),
    path('map/stops/nearest/', NearestStopView.as_view(), name='nearest-stop'),
    path('map/stops/nearby/', NearbyStopsView.as_view(), name='nearby-stops'),
    path('map/routes/employee/', EmployeeRoutesView.as_view(), name='employee-routes'),

    # Employee Management
    path('data-management/employees/upload-active/', hr_upload_active_employees, name='hr-upload-active-employees'),
    path('data-management/employees/upload-minimal/', hr_upload_minimal_employees, name='hr-upload-minimal-employees'),
    path('data-management/employees/delete/', hr_delete_employees, name='hr-delete-employees'),

    # Bus Stop Management
    path('data-management/bus-stops/upload/', hr_upload_bus_stops, name='hr-upload-busstops'),
    path('data-management/bus-stops/delete/', hr_delete_bus_stops, name='hr-delete-busstops'),

    # Coverage Mesh Management
    path('data-management/coverage-mesh/upload/', hr_upload_coverage_mesh, name='hr-upload-coverage'),
    path('data-management/coverage-mesh/delete/', hr_delete_coverage_mesh, name='hr-delete-coverage'),

    # Route Management
    path('data-management/routes/upload/', hr_upload_route_gpx, name='hr-upload-route'),
    path('data-management/routes/delete/', hr_delete_route, name='hr-delete-route'),

    path('', include(router.urls)),

    path('health/', health),
]