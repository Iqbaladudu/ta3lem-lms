"""
Serializers for Users API.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from users.models import StudentProfile, InstructorProfile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Basic user serializer for read operations.
    """
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 
            'full_name', 'role', 'avatar', 'bio', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserDetailSerializer(UserSerializer):
    """
    Detailed user serializer including profile information.
    """
    has_active_subscription = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + [
            'phone_number', 'date_of_birth', 'address', 'city', 
            'country', 'postal_code', 'timezone', 'language',
            'email_notifications', 'has_active_subscription', 'profile'
        ]
    
    def get_has_active_subscription(self, obj):
        return obj.has_active_subscription()
    
    def get_profile(self, obj):
        profile = obj.get_profile()
        if profile:
            if obj.role == User.STUDENT:
                return StudentProfileSerializer(profile).data
            elif obj.role == User.INSTRUCTOR:
                return InstructorProfileSerializer(profile).data
        return None


class StudentProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for student profile.
    """
    class Meta:
        model = StudentProfile
        fields = ['id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class InstructorProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for instructor profile.
    """
    class Meta:
        model = InstructorProfile
        fields = ['id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'role'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'role': {'required': False, 'default': User.STUDENT}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': "Passwords don't match."
            })
        return attrs
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    """
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'bio', 'phone_number',
            'date_of_birth', 'address', 'city', 'country',
            'postal_code', 'timezone', 'language', 'email_notifications'
        ]


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change.
    """
    old_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': "New passwords don't match."
            })
        return attrs


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer that includes user information.
    """
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims
        token['username'] = user.username
        token['email'] = user.email
        token['role'] = user.role
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add user information to response
        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
            'role': self.user.role,
            'full_name': self.user.get_full_name() or self.user.username,
        }
        
        return data


class AvatarUploadSerializer(serializers.ModelSerializer):
    """
    Serializer for avatar upload.
    """
    class Meta:
        model = User
        fields = ['avatar']
    
    def validate_avatar(self, value):
        # Validate file size (max 5MB)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Avatar file size must be less than 5MB.")
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                "Avatar must be a JPEG, PNG, GIF, or WebP image."
            )
        
        return value
