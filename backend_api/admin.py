from django.contrib import admin
from .models import BusStop, CoverageMesh, CoverageMeshPoint, RoutePlan, Route, RouteStopPoint, RouteTrackPoint

admin.site.register(BusStop)
admin.site.register(CoverageMesh)
admin.site.register(CoverageMeshPoint)
admin.site.register(RoutePlan)
admin.site.register(Route)
admin.site.register(RouteStopPoint)
admin.site.register(RouteTrackPoint)