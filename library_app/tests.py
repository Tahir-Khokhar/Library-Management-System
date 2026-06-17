from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient


from .models import Book, BorrowTransaction, Membership, MembershipPlan, BookSection


class LibraryAPITests(TestCase):
    def setUp(self) -> None:
        User = get_user_model()
        self.user = User.objects.create_user(username="alice", password="password123")

        # Obtain JWT tokens (requires simplejwt endpoints wired in auth_urls.py)
        self.client = APIClient()
        token_url = "/api/auth/token/"
        resp = self.client.post(token_url, {"username": "alice", "password": "password123"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.access_token = resp.json()["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        self.section = BookSection.objects.create(
            name="Kids - Story Books",
            slug="kids-stories-test",
            audience=BookSection.Audience.KIDS,
        )
        self.book = Book.objects.create(title="Test Book", author="Author", total_copies=1)
        self.book.sections.add(self.section)

    def test_membership_list_and_create(self):
        resp = self.client.get("/api/membership/")
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.json()["has_membership"])

        resp = self.client.post("/api/membership/", {"plan": "MONTH"}, format="json")
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp.json()["is_active"])


    def test_borrow_requires_active_membership(self):
        resp = self.client.post("/api/borrows/", {"book_id": self.book.id}, format="json")
        self.assertEqual(resp.status_code, 403)


    def test_borrow_requires_available_copies(self):
        Membership.create_for_user(self.user, MembershipPlan.MONTH)
        # Exhaust the only copy
        BorrowTransaction.objects.create(
            user=self.user,
            book=self.book,
            due_at=timezone.now() + timedelta(days=30),
        )

        resp = self.client.post("/api/borrows/", {"book_id": self.book.id}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertIn("detail", resp.json())


    def test_return_borrow_sets_fine_amount(self):
        Membership.create_for_user(self.user, MembershipPlan.MONTH)

        tx = BorrowTransaction.objects.create(
            user=self.user,
            book=self.book,
            borrowed_at=timezone.now() - timedelta(days=10),
            due_at=timezone.now() - timedelta(days=5),
        )
        self.assertFalse(tx.is_returned)

        resp = self.client.post("/api/return-borrow/", {"borrow_id": tx.id}, format="json")
        self.assertEqual(resp.status_code, 200)
        tx.refresh_from_db()
        self.assertTrue(tx.is_returned)
        self.assertGreaterEqual(float(tx.fine_amount), 0)


