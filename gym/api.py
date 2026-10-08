from rest_framework.viewsets import GenericViewSet
from rest_framework import mixins, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, BasePermission, SAFE_METHODS

from django.db.models import Avg, Count, Max, Min, Q
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
from django.contrib.auth import authenticate, login, logout
import pyotp

import openpyxl
from openpyxl import Workbook
from io import BytesIO
from django.http import HttpResponse

from gym.models import User, MembershipType, Membership, WorkoutSession
from gym.serializers import (
    UserSerializer,
    MembershipTypeSerializer,
    MembershipSerializer,
    WorkoutSessionSerializer,
)

class UserProfileViewSet(GenericViewSet):
    permission_classes = [IsAuthenticated]

    class LoginSerializer(serializers.Serializer):
        username = serializers.CharField()
        password = serializers.CharField()

    class OTPSerializer(serializers.Serializer):
        key = serializers.CharField()

    class OTPRequired(BasePermission):
        def has_permission(self, request, view):
            if not request.user or not request.user.is_authenticated:
                return False
            cache_key = f"otp_good:{request.user.id}"
            return bool(cache.get(cache_key, False))

    class OTPForEdit(BasePermission):
        def has_permission(self, request, view):
            if request.method in SAFE_METHODS:
                return True

            if request.method == "POST":
                return True

            if not request.user or not request.user.is_authenticated:
                return False

            cache_key = f"otp_good:{request.user.id}"
            return bool(cache.get(cache_key, False))

    @action(detail=False, url_path="info", methods=["GET"], permission_classes=[])
    def info(self, request, *args, **kwargs):
        auth_user = request.user
        is_auth = auth_user.is_authenticated

        data = {
            "is_authenticated": is_auth,
            "is_superuser": bool(auth_user.is_superuser) if is_auth else False,
            "username": auth_user.username if is_auth else None,
        }

        role = None
        domain_user = None

        if is_auth:
            try:
                domain_user = User.objects.get(account=auth_user)
                role = domain_user.role
            except User.DoesNotExist:
                domain_user = None
                role = None

        is_admin_role = role == getattr(User.Role, "ADMIN", "admin")
        is_admin = bool((is_auth and auth_user.is_superuser) or is_admin_role)

        data.update({
            "role": role,
            "is_admin": is_admin,
        })

        return Response(data)

    @action(
        detail=False,
        url_path="login",
        methods=["POST"],
        permission_classes=[],               
        serializer_class=LoginSerializer,
    )
    def user_login(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(request, username=username, password=password)
        if not user:
            return Response(
                {"success": False, "error": "Неверный логин или пароль"},
                status=400,
            )

        login(request, user)
        return Response({"success": True})

    @action(
        detail=False,
        url_path="logout",
        methods=["POST"],
        permission_classes=[IsAuthenticated],
    )
    def user_logout(self, request, *args, **kwargs):
        logout(request)
        return Response({"success": True})

    @action(detail=False, url_path="check-login", methods=["GET"], permission_classes=[])
    def get_check_login(self, request, *args, **kwargs):
        return Response({
            "is_authenticated": self.request.user.is_authenticated
        })
    @action(detail=False, url_path="otp-get-key", methods=["GET"])
    def otp_get_key(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"detail": "Authentication required"}, status=401)

        try:
            domain_user = User.objects.get(account=request.user)
        except User.DoesNotExist:
            return Response({"detail": "Нет связанного пользователя gym.User"}, status=400)

        if not domain_user.totp_key:
            domain_user.totp_key = pyotp.random_base32()
            domain_user.save()

        totp = pyotp.TOTP(domain_user.totp_key)
        url = totp.provisioning_uri(
            name=request.user.username or (request.user.email or "user"),
            issuer_name="GymApp",
        )

        return Response({"url": url})

    @action(
        detail=False,
        url_path="otp-login",
        methods=["POST"],
        serializer_class=OTPSerializer,
    )
    def otp_login(self, request, *args, **kwargs):
        """
        POST /api/userprofile/otp-login/
        { "key": "123456" }
        Проверка одноразового кода из приложения (Google Authenticator)
        """
        if not request.user.is_authenticated:
            return Response({"success": False, "error": "Not authenticated"}, status=401)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["key"]

        try:
            domain_user = User.objects.get(account=request.user)
        except User.DoesNotExist:
            return Response({"success": False, "error": "No gym.User for this account"}, status=400)

        if not domain_user.totp_key:
            return Response({"success": False, "error": "2FA not configured"}, status=400)

        totp = pyotp.TOTP(domain_user.totp_key)
        success = totp.verify(code)  

        if success:
            cache_key = f"otp_good:{request.user.id}"
            cache.set(cache_key, True, timeout=600) 

        return Response({"success": success})

    @action(
        detail=False,
        url_path="get-totp",
        methods=["GET"],
        permission_classes=[IsAuthenticated],
    )
    def get_totp(self, request, *args, **kwargs):
        secret = "JBSWY3DPEHPK3PXP"

        totp = pyotp.TOTP(secret)
        url = totp.provisioning_uri(
            name=request.user.username or "user",
            issuer_name="GymApp",
        )

        return Response({"url": url})
    @action(detail=False, url_path="otp-status")
    def get_otp_status(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            otp_good = False
        else:
            cache_key = f"otp_good:{self.request.user.id}"
            otp_good = cache.get(cache_key, False)

        return Response({"otp_good": otp_good})

    @action(detail=False, url_path="otp-required", permission_classes=[OTPRequired])
    def page_with_otp_required(self, *args, **kwargs):
        return Response({
            "success": True
        })


class UsersViewset(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "phone", "specialization", "role"]
    ordering_fields = ["name", "role"]
    ordering = ["name"]

    def get_queryset(self):
        qs = super().get_queryset()
        request_user = self.request.user
        if not request_user.is_authenticated:
            return qs.exclude(role=User.Role.ADMIN)

        current = None

        if request_user.is_authenticated:
            try:
                current = User.objects.get(account=request_user)
            except User.DoesNotExist:
                current = None

        is_admin_role = current and current.role == User.Role.ADMIN
        is_admin = (
            not request_user.is_authenticated
            or request_user.is_superuser
            or is_admin_role
)

        if is_admin:
            qs = qs.exclude(role=User.Role.ADMIN)
            role_param = self.request.query_params.get("role")
            if role_param in ("client", "trainer"):
                qs = qs.filter(role=role_param)
            return qs


        if current is None:
            return User.objects.none()

        if current.role == User.Role.CLIENT:
            return qs.exclude(role=User.Role.ADMIN).filter(
                Q(id=current.id) | Q(role=User.Role.TRAINER)
            )

        if current.role == User.Role.TRAINER:
            client_ids = (
                WorkoutSession.objects
                .filter(trainer=current)
                .values_list("client_id", flat=True)
                .distinct()
            )
            return qs.exclude(role=User.Role.ADMIN).filter(
                Q(id=current.id) | Q(id__in=client_ids)
            )

        return User.objects.none()
    
    @action(detail=False, methods=["GET"], url_path="export-excel")
    def export_excel(self, request, *args, **kwargs):
        qs = self.get_queryset()

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Users"

        ws.append(["ID", "ФИО", "Роль", "Телефон", "Специализация"])

        for u in qs:
            ws.append([
                u.id,
                u.name,
                u.get_role_display() if hasattr(u, "get_role_display") else u.role,
                u.phone or "",
                u.specialization or "",
            ])

        response = HttpResponse(
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        response["Content-Disposition"] = 'attachment; filename="users.xlsx"'

        wb.save(response)
        return response


class MembershipTypesViewset(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    queryset = MembershipType.objects.all()
    serializer_class = MembershipTypeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class MembershipsViewset(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    queryset = (
        Membership.objects
        .select_related("client", "membership_type")
        .all()
    )
    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        request_user = self.request.user
        if not request_user.is_authenticated:
            return qs

        current = None
        try:
            current = User.objects.get(account=request_user)
        except User.DoesNotExist:
            current = None

        is_admin_role = current and current.role == User.Role.ADMIN
        is_admin = request_user.is_superuser or is_admin_role

        if is_admin:
            owner_id = self.request.query_params.get("owner")
            if owner_id:
                qs = qs.filter(owner_id=owner_id)
            return qs

        if current is None:
            return Membership.objects.none()

        if current.role == User.Role.CLIENT:
            # клиент — только свои абонементы
            return qs.filter(client=current)

        if current.role == User.Role.TRAINER:
            # тренер — абонементы своих клиентов
            client_ids = (
                WorkoutSession.objects
                .filter(trainer=current)
                .values_list("client_id", flat=True)
                .distinct()
            )
            return qs.filter(client_id__in=client_ids)

        return Membership.objects.none()

class WorkoutSessionsViewset(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    queryset = (
        WorkoutSession.objects
        .select_related("client", "trainer")
        .all()
    )
    serializer_class = WorkoutSessionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = super().get_queryset()
        request_user = self.request.user
        if not request_user.is_authenticated:
            return qs

        current = None

        if request_user.is_authenticated:
            try:
                current = User.objects.get(account=request_user)
            except User.DoesNotExist:
                current = None

        is_admin_role = current and current.role == User.Role.ADMIN
        is_admin = (
            not request_user.is_authenticated
            or request_user.is_superuser
            or is_admin_role
        )

        if is_admin:
            return qs

        if current is None:
            return WorkoutSession.objects.none()

        if current.role == User.Role.CLIENT:
            return qs.filter(client=current)

        if current.role == User.Role.TRAINER:
            return qs.filter(trainer=current)

        return WorkoutSession.objects.none()
    


    #получить ключ
    #python
    #import pyotp
    #print(pyotp.TOTP("JBSWY3DPEHPK3PXP").now())
    #http://localhost:8000/api/user-profile/otp-status/
