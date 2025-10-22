from rest_framework import viewsets, mixins, status, filters
from rest_framework.decorators import action, api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser

from accounts.models import User
from .models import (
    BusStop,
    CoverageMesh,
    CoverageMeshPoint,
    RoutePlan,
    Route,
    RouteStopPoint,
    RouteTrackPoint,
)
from .serializers import (
    UserListSerializer,
    UserUpdateSerializer,
    BusStopSerializer,
    CoverageMeshSerializer,
    RoutePlanSerializer,
)

from math import radians, sin, cos, asin, sqrt
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator

import csv
import json
import uuid
from io import StringIO
import xml.etree.ElementTree as ET

# ============================
# Existing ViewSets/APIs
# ============================

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-created_at')
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['partial_update', 'update']:
            return UserUpdateSerializer
        return UserListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        shift = self.request.query_params.get('shift')
        company = self.request.query_params.get('company')
        is_active = self.request.query_params.get('is_active')
        employee_status = self.request.query_params.get('employee_status')
        if shift:
            qs = qs.filter(shift=shift)
        if company:
            qs = qs.filter(company=company)
        if is_active in ['true', 'false']:
            qs = qs.filter(is_active=(is_active == 'true'))
        if employee_status:
            qs = qs.filter(employee_status=employee_status)
        return qs

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = UserListSerializer(request.user)
        return Response(serializer.data)


class BusStopViewSet(viewsets.ModelViewSet):
    queryset = BusStop.objects.all().order_by('stop_id')
    serializer_class = BusStopSerializer
    permission_classes = [IsAuthenticated]


class CoverageMeshViewSet(mixins.CreateModelMixin,
                          mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    queryset = CoverageMesh.objects.all().order_by('-created_at')
    serializer_class = CoverageMeshSerializer
    permission_classes = [IsAuthenticated]


class RoutePlanViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       viewsets.GenericViewSet):
    queryset = RoutePlan.objects.prefetch_related('routes__stops', 'routes__trackpoints').all().order_by('-created_at')
    serializer_class = RoutePlanSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def active(self, request):
        plan = RoutePlan.objects.prefetch_related('routes__stops', 'routes__trackpoints').filter(is_active=True).first()
        if not plan:
            return Response({'detail': 'No active plan'}, status=status.HTTP_204_NO_CONTENT)
        return Response(self.get_serializer(plan).data)


def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    dlat = radians(lat2 - lat1)
    dlon = radians(l2 := lon2) - radians(lon1)  # minor refactor to avoid re-parsing
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c


class EmployeeLocationView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        u = request.user
        if u.latitude is None or u.longitude is None:
            return Response({'detail': 'No registered location'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'lat': u.latitude, 'lng': u.longitude})


class NearestStopView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        u = request.user
        if u.latitude is None or u.longitude is None:
            return Response({'detail': 'No registered location'}, status=status.HTTP_404_NOT_FOUND)
        stops = list(BusStop.objects.filter(is_active=True))
        if not stops:
            return Response({'detail': 'No stops available'}, status=status.HTTP_404_NOT_FOUND)
        best = min(stops, key=lambda s: haversine_m(u.latitude, u.longitude, s.latitude, s.longitude))
        distance_m = haversine_m(u.latitude, u.longitude, best.latitude, best.longitude)
        data = BusStopSerializer(best).data
        return Response({'stop': {
            'id': data['id'],
            'name': data['name'],
            'latitude': data['latitude'],
            'longitude': data['longitude'],
        }, 'distance_m': distance_m})


class NearbyStopsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        u = request.user
        limit = int(request.query_params.get('limit', 100))
        qs = BusStop.objects.filter(is_active=True)
        if u.latitude is None or u.longitude is None:
            stops = qs.order_by('stop_id')[:limit]
            return Response(BusStopSerializer(stops, many=True).data)
        stops = list(qs)
        stops.sort(key=lambda s: haversine_m(u.latitude, u.longitude, s.latitude, s.longitude))
        return Response(BusStopSerializer(stops[:limit], many=True).data)


class EmployeeRoutesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        plan = RoutePlan.objects.prefetch_related('routes__stops', 'routes__trackpoints').filter(is_active=True).first()
        if not plan:
            return Response({'routes': []})
        return Response(RoutePlanSerializer(plan).data)


# ============================
# Existing ViewSets/APIs
# ============================

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 200


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('-created_at')
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    # Enable server-side ordering; optional search via 'q' implemented in get_queryset
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['created_at', 'username', 'email', 'employee_id', 'company', 'shift', 'is_active']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ['partial_update', 'update']:
            return UserUpdateSerializer
        return UserListSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        shift = self.request.query_params.get('shift')
        company = self.request.query_params.get('company')
        is_active = self.request.query_params.get('is_active')
        employee_status = self.request.query_params.get('employee_status')
        # Optional lightweight search param 'q'
        q = self.request.query_params.get('q')
        if q:
            needle = q.strip()
            qs = qs.filter(
                Q(username__icontains=needle) |
                Q(email__icontains=needle) |
                Q(employee_id__icontains=needle) |
                Q(company__icontains=needle)
            )
        if shift:
            qs = qs.filter(shift=shift)
        if company:
            qs = qs.filter(company=company)
        if is_active in ['true', 'false']:
            qs = qs.filter(is_active=(is_active == 'true'))
        if employee_status:
            qs = qs.filter(employee_status=employee_status)
        return qs

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = UserListSerializer(request.user)
        return Response(serializer.data)


class BusStopViewSet(viewsets.ModelViewSet):
    queryset = BusStop.objects.all().order_by('stop_id')
    serializer_class = BusStopSerializer
    permission_classes = [IsAuthenticated]


class CoverageMeshViewSet(mixins.CreateModelMixin,
                          mixins.ListModelMixin,
                          viewsets.GenericViewSet):
    queryset = CoverageMesh.objects.all().order_by('-created_at')
    serializer_class = CoverageMeshSerializer
    permission_classes = [IsAuthenticated]


class RoutePlanViewSet(mixins.ListModelMixin,
                       mixins.RetrieveModelMixin,
                       viewsets.GenericViewSet):
    queryset = RoutePlan.objects.prefetch_related('routes__stops', 'routes__trackpoints').all().order_by('-created_at')
    serializer_class = RoutePlanSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def active(self, request):
        plan = RoutePlan.objects.prefetch_related('routes__stops', 'routes__trackpoints').filter(is_active=True).first()
        if not plan:
            return Response({'detail': 'No active plan'}, status=status.HTTP_204_NO_CONTENT)
        return Response(self.get_serializer(plan).data)


def haversine_m(lat1, lon1, lat2, lon2):
    R = 6371000.0
    dlat = radians(lat2 - lat1)
    dlon = radians(l2 := lon2) - radians(lon1)  # minor refactor to avoid re-parsing
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return R * c


class EmployeeLocationView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        u = request.user
        if u.latitude is None or u.longitude is None:
            return Response({'detail': 'No registered location'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'lat': u.latitude, 'lng': u.longitude})


class NearestStopView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        u = request.user
        if u.latitude is None or u.longitude is None:
            return Response({'detail': 'No registered location'}, status=status.HTTP_404_NOT_FOUND)
        stops = list(BusStop.objects.filter(is_active=True))
        if not stops:
            return Response({'detail': 'No stops available'}, status=status.HTTP_404_NOT_FOUND)
        best = min(stops, key=lambda s: haversine_m(u.latitude, u.longitude, s.latitude, s.longitude))
        distance_m = haversine_m(u.latitude, u.longitude, best.latitude, best.longitude)
        data = BusStopSerializer(best).data
        return Response({'stop': {
            'id': data['id'],
            'name': data['name'],
            'latitude': data['latitude'],
            'longitude': data['longitude'],
        }, 'distance_m': distance_m})


class NearbyStopsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        u = request.user
        limit = int(request.query_params.get('limit', 100))
        qs = BusStop.objects.filter(is_active=True)
        if u.latitude is None or u.longitude is None:
            stops = qs.order_by('stop_id')[:limit]
            return Response(BusStopSerializer(stops, many=True).data)
        stops = list(qs)
        stops.sort(key=lambda s: haversine_m(u.latitude, u.longitude, s.latitude, s.longitude))
        return Response(BusStopSerializer(stops[:limit], many=True).data)


class EmployeeRoutesView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        plan = RoutePlan.objects.prefetch_related('routes__stops', 'routes__trackpoints').filter(is_active=True).first()
        if not plan:
            return Response({'routes': []})
        return Response(RoutePlanSerializer(plan).data)


# ============================
# HR/Admin Data Management APIs (unchanged from your version)
# ============================

def _user_role(user):
    try:
        if hasattr(user, 'role') and user.role:
            return str(user.role).upper()
    except Exception:
        pass
    return "GUEST"


def _hr_or_master_required(fn):
    def wrapper(request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return JsonResponse({"detail": "Authentication required"}, status=401)
        role = _user_role(request.user)
        if role not in ["HR_ADMIN", "MASTER_ADMIN"]:
            return JsonResponse({"detail": "Forbidden"}, status=403)
        return fn(request, *args, **kwargs)
    return wrapper


@_hr_or_master_required
def hr_dm_overview(request):
    """Main data management dashboard API - uses User model as employees"""
    role = _user_role(request.user)

    q = request.GET.get("q", "")
    sort_field = request.GET.get("sort", "employee_id")
    dir_ = request.GET.get("dir", "asc").lower()
    show_all = str(request.GET.get("show_all", "0")).lower() in ["1", "true", "yes"]

    sort_map = {
        "employee_id": "employee_id",
        "name": "name",
        "company": "company",
    }
    actual_sort = sort_map.get(sort_field, "employee_id")
    sort = actual_sort if dir_ == "asc" else f"-{actual_sort}"

    qs = User.objects.all()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(employee_id__icontains=q))
    qs = qs.order_by(sort)

    if show_all:
        employees_payload = list(qs.values(
            'id', 'employee_id', 'name', 'email', 'company', 'shift',
            'latitude', 'longitude', 'is_active', 'created_at'
        ))
        total_pages = 1
    else:
        page = int(request.GET.get("page", 1))
        paginator = Paginator(qs, 10)
        page_obj = paginator.get_page(page)
        employees_payload = list(page_obj.object_list.values(
            'id', 'employee_id', 'name', 'email', 'company', 'shift',
            'latitude', 'longitude', 'is_active', 'created_at'
        ))
        total_pages = paginator.num_pages

    bus_stops_count = BusStop.objects.count()
    bus_stops_active = BusStop.objects.filter(is_active=True).count()

    coverage_meshes = CoverageMesh.objects.all()
    coverage_summary = [
        {
            "id": mesh.id,
            "name": mesh.name,
            "version": mesh.version,
            "points_count": mesh.points.count(),
            "created_at": str(mesh.created_at)
        }
        for mesh in coverage_meshes
    ]

    route_plans = RoutePlan.objects.all()
    route_summary = [
        {
            "id": plan.id,
            "route_plan_name": plan.route_plan_name,
            "bus_supplier": plan.bus_supplier,
            "is_active": plan.is_active,
            "routes_count": plan.routes.count(),
            "created_at": str(plan.created_at)
        }
        for plan in route_plans
    ]

    data = {
        "role": role,
        "employees": {
            "results": employees_payload,
            "total_pages": total_pages,
            "total_count": qs.count()
        },
        "bus_stops": {
            "total": bus_stops_count,
            "active": bus_stops_active,
            "inactive": bus_stops_count - bus_stops_active
        },
        "coverage_meshes": coverage_summary,
        "route_plans": route_summary,
    }
    return JsonResponse(data)


@_hr_or_master_required
@parser_classes([MultiPartParser, FormParser])
def hr_upload_active_employees(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    f = request.FILES.get("active_employees_file")
    if not f:
        return JsonResponse({"detail": "No file"}, status=400)

    try:
        import pandas as pd
        decoded = f.read().decode("iso-8859-1")
        df = pd.read_csv(StringIO(decoded))
        df.columns = [c.strip().lower() for c in df.columns]

        if 'numero de personal' not in df.columns:
            return JsonResponse({"detail": "Column 'Numero de personal' not found."}, status=400)

        active_ids = set(df['numero de personal'].astype(str))
        updated = 0

        for user in User.objects.all():
            if hasattr(user, 'employee_id') and user.employee_id:
                new_active = user.employee_id in active_ids
                if user.is_active != new_active:
                    user.is_active = new_active
                    user.save()
                    updated += 1

        return JsonResponse({"updated": updated})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@_hr_or_master_required
@parser_classes([MultiPartParser, FormParser])
def hr_upload_minimal_employees(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    csv_file = request.FILES.get("csv_file")
    if not csv_file:
        return JsonResponse({"detail": "No file"}, status=400)

    try:
        decoded = csv_file.read().decode("utf-8").splitlines()
        reader = csv.reader(decoded)
        created = 0

        for row in reader:
            if len(row) < 6:
                continue
            employee_id, company, utilization, shift, lat_str, lon_str = row[:6]

            try:
                lat = float(lat_str)
                lon = float(lon_str)
            except Exception:
                continue

            if User.objects.filter(employee_id=employee_id).exists():
                continue

            User.objects.create(
                username=f"emp_{uuid.uuid4().hex[:8]}",
                email=f"emp_{employee_id}@temp.com",
                employee_id=employee_id,
                name=f"Employee {employee_id}",
                company=str(company),
                shift=str(shift),
                latitude=lat,
                longitude=lon,
                is_active=True,
            )
            created += 1

        return JsonResponse({"created": created})
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@_hr_or_master_required
def hr_delete_employees(request):
    if request.method != "POST":
        return JsonResponse({"deleted": 0})

    try:
        body = json.loads(request.body.decode()) if request.body else {}
    except Exception:
        body = {}

    ids = body.get("selected_ids") or request.POST.getlist("selected_ids")
    if not ids:
        return JsonResponse({"deleted": 0})

    deleted, _ = User.objects.filter(id__in=ids).delete()
    return JsonResponse({"deleted": deleted})


@_hr_or_master_required
@parser_classes([MultiPartParser, FormParser])
def hr_upload_bus_stops(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    file = request.FILES.get("bus_stop_file")
    if not file:
        return JsonResponse({"detail": "No file"}, status=400)

    try:
        import pandas as pd
        df = pd.read_csv(StringIO(file.read().decode("utf-8")))
        df.columns = [c.strip().lower() for c in df.columns]

        required = ['stop_id', 'name', 'latitude', 'longitude']
        if not all(col in df.columns for col in required):
            return JsonResponse({"detail": "CSV missing required columns: stop_id, name, latitude, longitude"}, status=400)

        BusStop.objects.all().delete()

        objs = []
        for _, row in df.iterrows():
            objs.append(BusStop(
                stop_id=str(row['stop_id']),
                name=str(row['name']),
                latitude=float(row['latitude']),
                longitude=float(row['longitude']),
                source=row.get('source', 'Generated')
            ))

        BusStop.objects.bulk_create(objs)

        return JsonResponse({
            "uploaded": len(objs),
            "message": f"Successfully uploaded {len(objs)} bus stops"
        })
    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@_hr_or_master_required
def hr_delete_bus_stops(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    count = BusStop.objects.count()
    BusStop.objects.all().delete()
    return JsonResponse({"status": "ok", "deleted": count})


@_hr_or_master_required
@parser_classes([MultiPartParser, FormParser])
def hr_upload_coverage_mesh(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    file = request.FILES.get("coverage_mesh_file")
    mesh_name = request.POST.get("name", "Coverage Mesh")
    mesh_version = request.POST.get("version", "1.0")

    if not file:
        return JsonResponse({"detail": "No file"}, status=400)

    try:
        content = file.read().decode("utf-8")

        try:
            data = json.loads(content)
            coordinates = []

            if data.get("type") == "FeatureCollection":
                for feature in data.get("features", []):
                    geom = feature.get("geometry", {})
                    if geom.get("type") == "Polygon":
                        coordinates.extend(geom.get("coordinates", [[]])[0])
            elif data.get("type") == "Polygon":
                coordinates = data.get("coordinates", [[]])[0]

            points = [(lon, lat) for lon, lat in coordinates]

        except json.JSONDecodeError:
            import pandas as pd
            df = pd.read_csv(StringIO(content))
            df.columns = [c.strip().lower() for c in df.columns]

            if 'latitude' not in df.columns or 'longitude' not in df.columns:
                return JsonResponse({"detail": "CSV must have latitude and longitude columns"}, status=400)

            points = [(row['longitude'], row['latitude']) for _, row in df.iterrows()]

        mesh = CoverageMesh.objects.create(
            name=mesh_name,
            version=mesh_version
        )

        mesh_points = [
            CoverageMeshPoint(
                mesh=mesh,
                longitude=lon,
                latitude=lat,
                order=i
            )
            for i, (lon, lat) in enumerate(points)
        ]
        CoverageMeshPoint.objects.bulk_create(mesh_points)

        return JsonResponse({
            "status": "ok",
            "mesh_id": mesh.id,
            "points_count": len(mesh_points),
            "message": f"Successfully uploaded coverage mesh with {len(mesh_points)} points"
        })

    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@_hr_or_master_required
def hr_delete_coverage_mesh(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    try:
        body = json.loads(request.body.decode()) if request.body else {}
    except Exception:
        body = {}

    mesh_id = body.get("mesh_id") or request.POST.get("mesh_id")

    if mesh_id:
        deleted, _ = CoverageMesh.objects.filter(id=mesh_id).delete()
    else:
        deleted, _ = CoverageMesh.objects.all().delete()

    return JsonResponse({"status": "ok", "deleted": deleted})


@_hr_or_master_required
@parser_classes([MultiPartParser, FormParser])
def hr_upload_route_gpx(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    file = request.FILES.get('route_file')
    route_name = request.POST.get('name')
    shift_type = request.POST.get('route_type', 'FIXED_8HRS')
    is_active = request.POST.get('is_active') == 'on'
    plan_name = request.POST.get('plan_name', f"{route_name} Plan")
    bus_supplier = request.POST.get('bus_supplier', '')

    if not file or not route_name:
        return JsonResponse({"detail": "Missing file or route name"}, status=400)

    try:
        content = file.read().decode('utf-8')
        root = ET.fromstring(content)
        ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}

        trkpts = root.findall('.//gpx:trkpt', ns)
        if not trkpts:
            trkpts = root.findall('.//trkpt')

        rte_points = root.findall('.//gpx:rte/gpx:rtept', ns)
        if not rte_points:
            rte_points = root.findall('.//gpx:wpt', ns)
        if not rte_points:
            rte_points = root.findall('.//rtept')
        if not rte_points:
            rte_points = root.findall('.//wpt')

        plan, created = RoutePlan.objects.get_or_create(
            route_plan_name=plan_name,
            defaults={
                'bus_supplier': bus_supplier,
                'is_active': is_active
            }
        )

        if not created and is_active:
            RoutePlan.objects.filter(is_active=True).update(is_active=False)
            plan.is_active = True
            plan.save()

        route = Route.objects.create(
            plan=plan,
            route_name=route_name,
            shift=shift_type
        )

        track_points = []
        for i, pt in enumerate(trkpts):
            track_points.append(RouteTrackPoint(
                route=route,
                latitude=float(pt.attrib['lat']),
                longitude=float(pt.attrib['lon']),
                order=i
            ))
        RouteTrackPoint.objects.bulk_create(track_points)

        stop_points = []
        for i, pt in enumerate(rte_points):
            name_elem = pt.find('gpx:name', ns) or pt.find('name')
            stop_name = name_elem.text if name_elem is not None else f"Stop {i+1}"

            stop_points.append(RouteStopPoint(
                route=route,
                stop_name=stop_name,
                latitude=float(pt.attrib['lat']),
                longitude=float(pt.attrib['lon']),
                order=i
            ))
        RouteStopPoint.objects.bulk_create(stop_points)

        return JsonResponse({
            "status": "ok",
            "route_id": route.id,
            "plan_id": plan.id,
            "track_points": len(track_points),
            "stop_points": len(stop_points),
            "message": f"Successfully uploaded route '{route_name}' with {len(track_points)} track points and {len(stop_points)} stops"
        })

    except Exception as e:
        return JsonResponse({"detail": str(e)}, status=500)


@_hr_or_master_required
def hr_delete_route(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    try:
        body = json.loads(request.body.decode()) if request.body else {}
    except Exception:
        body = {}

    route_id = body.get("route_id") or request.POST.get("route_id")
    plan_id = body.get("plan_id") or request.POST.get("plan_id")

    deleted_count = 0

    if route_id:
        deleted, _ = Route.objects.filter(id=route_id).delete()
        deleted_count += deleted

    if plan_id:
        deleted, _ = RoutePlan.objects.filter(id=plan_id).delete()
        deleted_count += deleted

    if not route_id and not plan_id:
        return JsonResponse({"detail": "route_id or plan_id required"}, status=400)

    return JsonResponse({"status": "ok", "deleted": deleted_count})

def health(request):
    return HttpResponse("ok", status=200)