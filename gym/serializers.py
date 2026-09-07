from rest_framework import serializers
from gym.models import User, MembershipType, Membership, WorkoutSession
from django.contrib.auth import get_user_model

AuthUser = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = User
        fields = "__all__" 
        read_only_fields = ("account",)

    def create(self, validated_data):
        username = validated_data.pop("username", "").strip()
        password = validated_data.pop("password", "").strip()

        account = None
        if username and password:
            account = AuthUser.objects.create_user(
                username=username,
                password=password,
            )

        validated_data["account"] = account
        return super().create(validated_data)

class MembershipTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MembershipType
        fields = "__all__"

class MembershipSerializer(serializers.ModelSerializer):
    client = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role="client")
    )
    membership_type = serializers.PrimaryKeyRelatedField(
        queryset=MembershipType.objects.all()
    )

    class Meta:
        model = Membership
        fields = "__all__"         
        read_only_fields = ("owner",)

    def create(self, validated_data):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["owner"] = request.user
        return super().create(validated_data)


class WorkoutSessionSerializer(serializers.ModelSerializer):
    client = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role="client")
    )
    trainer = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role="trainer")
    )

    class Meta:
        model = WorkoutSession
        fields = "__all__"
