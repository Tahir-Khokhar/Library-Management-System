from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.views import APIView

from rest_framework.response import Response

from .models import Book, BorrowTransaction, Membership, MembershipPlan
from .serializers import (
    BorrowRequestSerializer,
    BorrowTransactionSerializer,
    MembershipCreateSerializer,
    MembershipSerializer,
)


class IsActiveMembership(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return Membership.objects.filter(user=request.user, is_active=True).filter(
            start_date__lte=timezone.now(), end_date__gte=timezone.now()
        ).exists()


class MembershipViewSet(viewsets.ViewSet):

    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        qs = Membership.objects.filter(user=request.user).order_by("-created_at")
        serializer = MembershipSerializer(qs.first(), context={}) if qs.exists() else None
        if not qs.exists():
            return Response({"has_membership": False}, status=status.HTTP_200_OK)

        membership = qs.first()
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
        books = Book.objects.all().order_by("id")
        # simple inline serializer to avoid extra file
        data = [
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "total_copies": b.total_copies,
                "available_copies": b.currently_available_copies,
            }
            for b in books
        ]
        return Response({"books": data}, status=status.HTTP_200_OK)


class BorrowViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated, IsActiveMembership]

    def create(self, request):
        req = BorrowRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)

        book = get_object_or_404(Book, id=req.validated_data["book_id"])

        if book.currently_available_copies <= 0:
            return Response(
                {"detail": "No available copies for this book"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        now = timezone.now()
        due_at = now + timezone.timedelta(days=30)

        tx = BorrowTransaction.objects.create(
            user=request.user,
            book=book,
            due_at=due_at,
        )
        return Response(BorrowTransactionSerializer(tx).data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        tx = get_object_or_404(BorrowTransaction, pk=pk, user=request.user)
        return Response(BorrowTransactionSerializer(tx).data)


class ReturnBorrowViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request):
        tx_id = request.data.get("borrow_id")
        tx = get_object_or_404(BorrowTransaction, pk=tx_id, user=request.user)
        if tx.is_returned:
            return Response({"detail": "Already returned"}, status=status.HTTP_400_BAD_REQUEST)

        tx.return_book()
        return Response(BorrowTransactionSerializer(tx).data, status=status.HTTP_200_OK)


class MyTransactionsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        txs = BorrowTransaction.objects.filter(user=request.user).order_by("-borrowed_at")
        return Response(BorrowTransactionSerializer(txs, many=True).data)

