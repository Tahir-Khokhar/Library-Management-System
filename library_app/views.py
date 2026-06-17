from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Book, BorrowTransaction, Membership

from .serializers import (
    BorrowRequestSerializer,
    BorrowTransactionSerializer,
    BookSerializer,
    MembershipCreateSerializer,
    MembershipSerializer,
)


class IsActiveMembership(permissions.BasePermission):
    """User must have a currently valid active membership."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        now = timezone.now()
        return Membership.objects.filter(
            user=request.user,
            is_active=True,
            start_date__lte=now,
            end_date__gte=now,
        ).exists()


class MembershipViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        membership = (
            Membership.objects.filter(user=request.user)
            .order_by("-created_at")
            .first()
        )

        if membership is None:
            return Response({"has_membership": False}, status=status.HTTP_200_OK)

        return Response(
            {
                "has_membership": membership.is_currently_valid(),
                "membership": MembershipSerializer(membership).data,
            },
            status=status.HTTP_200_OK,
        )

    def create(self, request):
        serializer = MembershipCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan = serializer.validated_data["plan"]
        membership = Membership.create_for_user(request.user, plan)
        return Response(MembershipSerializer(membership).data, status=status.HTTP_201_CREATED)


class BookViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        qs = Book.objects.all().order_by("id")
        serializer = BookSerializer(qs, many=True)
        return Response({"books": serializer.data}, status=status.HTTP_200_OK)


class BorrowViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsActiveMembership]

    def create(self, request):
        serializer = BorrowRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        book = get_object_or_404(Book, id=serializer.validated_data["book_id"])
        if book.currently_available_copies <= 0:
            raise ValidationError({"detail": "No available copies for this book"})

        due_at = timezone.now() + timezone.timedelta(days=30)
        tx = BorrowTransaction.objects.create(
            user=request.user,
            book=book,
            due_at=due_at,
        )
        return Response(BorrowTransactionSerializer(tx).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        tx = get_object_or_404(BorrowTransaction, pk=pk, user=request.user)
        return Response(BorrowTransactionSerializer(tx).data, status=status.HTTP_200_OK)


class ReturnBorrowViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        tx_id = request.data.get("borrow_id")
        if tx_id is None:
            raise ValidationError({"borrow_id": "This field is required."})

        tx = get_object_or_404(BorrowTransaction, pk=tx_id, user=request.user)
        if tx.is_returned:
            raise ValidationError({"detail": "Already returned"})

        tx.return_book()
        return Response(BorrowTransactionSerializer(tx).data, status=status.HTTP_200_OK)


class MyTransactionsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        txs = BorrowTransaction.objects.filter(user=request.user).order_by("-borrowed_at")
        serializer = BorrowTransactionSerializer(txs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


