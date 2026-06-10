from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Book, BorrowTransaction, Membership, MembershipPlan


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class MembershipSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Membership
        fields = [
            "id",
            "user",
            "plan",
            "start_date",
            "end_date",
            "is_active",
            "created_at",
        ]


class MembershipCreateSerializer(serializers.Serializer):
    plan = serializers.ChoiceField(choices=[(p.value, p.name) for p in MembershipPlan])

    def validate_plan(self, value):
        # value comes as the enum value (e.g. 'MONTH')
        try:
            return MembershipPlan(value)
        except ValueError:
            raise serializers.ValidationError("Invalid plan")


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            "id",
            "title",
            "author",
            "total_copies",
        ]



class BorrowRequestSerializer(serializers.Serializer):
    book_id = serializers.IntegerField()


class BorrowTransactionSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    book = BookSerializer(read_only=True)

    class Meta:
        model = BorrowTransaction
        fields = [
            "id",
            "user",
            "book",
            "borrowed_at",
            "due_at",
            "returned_at",
            "is_returned",
            "fine_amount",
            "fine_paid",
        ]

