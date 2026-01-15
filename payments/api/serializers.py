"""
Serializers for Payments API.
"""

from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType

from payments.models import Order, PaymentProvider, BankAccount
from users.api.serializers import UserSerializer


class PaymentProviderSerializer(serializers.ModelSerializer):
    """
    Serializer for PaymentProvider model.
    """
    class Meta:
        model = PaymentProvider
        fields = [
            'id', 'name', 'provider_type', 'display_name', 'description',
            'icon', 'supports_subscription', 'supports_refund',
            'supported_currencies', 'min_amount', 'max_amount', 'is_active'
        ]
        read_only_fields = ['id']


class BankAccountSerializer(serializers.ModelSerializer):
    """
    Serializer for BankAccount model.
    """
    class Meta:
        model = BankAccount
        fields = [
            'id', 'bank_name', 'bank_code', 'account_number',
            'account_holder', 'branch', 'logo', 'instructions', 'is_active'
        ]
        read_only_fields = ['id']


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Order model.
    """
    user = UserSerializer(read_only=True)
    payment_provider = PaymentProviderSerializer(read_only=True)
    item_name = serializers.SerializerMethodField()
    formatted_total = serializers.SerializerMethodField()
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'user', 'order_type', 'item_name',
            'subtotal', 'discount_amount', 'tax_amount', 'total_amount',
            'formatted_total', 'currency', 'payment_provider', 'status',
            'gateway_order_id', 'created_at', 'paid_at', 'expires_at',
            'is_expired'
        ]
        read_only_fields = [
            'id', 'order_number', 'user', 'created_at', 'paid_at'
        ]
    
    def get_item_name(self, obj):
        if obj.item:
            return obj.item.get_display_name() if hasattr(obj.item, 'get_display_name') else str(obj.item)
        return None
    
    def get_formatted_total(self, obj):
        return obj.get_formatted_total()
    
    def get_is_expired(self, obj):
        return obj.is_expired()


class OrderDetailSerializer(OrderSerializer):
    """
    Detailed serializer for Order including bank account info.
    """
    bank_account = BankAccountSerializer(read_only=True)
    
    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + [
            'bank_account', 'transfer_amount', 'transfer_date',
            'transfer_notes', 'payment_proof', 'verification_notes',
            'rejection_reason', 'verified_at', 'updated_at'
        ]


class OrderCreateSerializer(serializers.Serializer):
    """
    Serializer for creating orders.
    """
    order_type = serializers.ChoiceField(choices=['course', 'subscription'])
    item_id = serializers.IntegerField()
    payment_provider_id = serializers.IntegerField(required=False)
    
    def validate(self, attrs):
        order_type = attrs['order_type']
        item_id = attrs['item_id']
        
        # Validate item exists
        if order_type == 'course':
            from courses.models import Course
            try:
                item = Course.objects.get(pk=item_id, status='published')
                if item.is_free:
                    raise serializers.ValidationError(
                        "This course is free and doesn't require payment."
                    )
            except Course.DoesNotExist:
                raise serializers.ValidationError("Course not found.")
        elif order_type == 'subscription':
            from subscriptions.models import SubscriptionPlan
            try:
                item = SubscriptionPlan.objects.get(pk=item_id, is_active=True)
            except SubscriptionPlan.DoesNotExist:
                raise serializers.ValidationError("Subscription plan not found.")
        
        attrs['item'] = item
        return attrs


class PaymentProofUploadSerializer(serializers.Serializer):
    """
    Serializer for uploading payment proof.
    """
    payment_proof = serializers.ImageField()
    transfer_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    transfer_date = serializers.DateField()
    transfer_notes = serializers.CharField(required=False, allow_blank=True)
    
    def validate_payment_proof(self, value):
        # Validate file size (max 5MB)
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("File size must be less than 5MB.")
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                "File must be a JPEG, PNG, GIF, or WebP image."
            )
        
        return value


class OrderStatusSerializer(serializers.Serializer):
    """
    Serializer for order status response.
    """
    order_number = serializers.CharField()
    status = serializers.CharField()
    status_display = serializers.CharField()
    is_paid = serializers.BooleanField()
    is_expired = serializers.BooleanField()
    can_upload_proof = serializers.BooleanField()
    next_action = serializers.CharField(allow_null=True)


class CheckoutResponseSerializer(serializers.Serializer):
    """
    Serializer for checkout response.
    """
    success = serializers.BooleanField()
    order = OrderSerializer()
    available_providers = PaymentProviderSerializer(many=True)
    bank_accounts = BankAccountSerializer(many=True, required=False)


class WebhookPayloadSerializer(serializers.Serializer):
    """
    Base serializer for webhook payloads.
    """
    event_type = serializers.CharField(required=False)
    order_id = serializers.CharField(required=False)
    transaction_id = serializers.CharField(required=False)
    status = serializers.CharField(required=False)
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    
    # Allow additional fields
    class Meta:
        extra_kwargs = {'non_field_errors': {'allow_blank': True}}
