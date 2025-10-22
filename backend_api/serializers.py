from rest_framework import serializers
from accounts.models import User
from .models import BusStop, CoverageMesh, CoverageMeshPoint, RoutePlan, Route, RouteStopPoint, RouteTrackPoint

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'role', 'employee_id', 'company',
            'is_active', 'active_as_of', 'employee_status', 'shift', 'utilization',
            'latitude', 'longitude', 'street_name', 'address_number', 'neighborhood',
            'postal_code', 'district', 'state', 'country', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'email', 'utilization',
            'street_name', 'address_number', 'neighborhood', 'postal_code',
            'district', 'state', 'country', 'latitude', 'longitude',
            'shift'
        ]

class BusStopSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusStop
        fields = ['id', 'stop_id', 'name', 'latitude', 'longitude', 'source', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

class CoverageMeshPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = CoverageMeshPoint
        fields = ['latitude', 'longitude', 'order']

class CoverageMeshSerializer(serializers.ModelSerializer):
    points = CoverageMeshPointSerializer(many=True)
    class Meta:
        model = CoverageMesh
        fields = ['id', 'name', 'version', 'created_at', 'points']
        read_only_fields = ['id', 'created_at']
    def create(self, validated_data):
        points = validated_data.pop('points', [])
        mesh = CoverageMesh.objects.create(**validated_data)
        CoverageMeshPoint.objects.bulk_create([
            CoverageMeshPoint(mesh=mesh, **pt) for pt in points
        ])
        return mesh

class RouteTrackPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteTrackPoint
        fields = ['latitude', 'longitude', 'order']

class RouteStopPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = RouteStopPoint
        fields = ['stop_name', 'latitude', 'longitude', 'order']

class RouteSerializer(serializers.ModelSerializer):
    stops = RouteStopPointSerializer(many=True, read_only=True)
    trackpoints = RouteTrackPointSerializer(many=True, read_only=True)
    class Meta:
        model = Route
        fields = ['id', 'route_name', 'shift', 'color', 'stops', 'trackpoints']

class RoutePlanSerializer(serializers.ModelSerializer):
    routes = RouteSerializer(many=True, read_only=True)
    class Meta:
        model = RoutePlan
        fields = ['id', 'route_plan_name', 'bus_supplier', 'is_active', 'created_at', 'routes']
        read_only_fields = ['id', 'created_at']

class RunOptimizationSerializer(serializers.Serializer):
    pass