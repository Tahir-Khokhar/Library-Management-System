from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class MembershipPlan(models.TextChoices):
    MONTH = "MONTH", "1 Month"
    YEAR = "YEAR", "1 Year"


class Membership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    plan = models.CharField(max_length=10, choices=MembershipPlan.choices)

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} {self.plan} {'active' if self.is_active else 'inactive'}"

    @classmethod
    def create_for_user(cls, user, plan: MembershipPlan) -> "Membership":
        now = timezone.now()
        if plan == MembershipPlan.MONTH:
            end = now + timedelta(days=30)
        elif plan == MembershipPlan.YEAR:
            end = now + timedelta(days=365)
        else:
            raise ValueError("Invalid membership plan")

        # Deactivate old active memberships
        cls.objects.filter(user=user, is_active=True).update(is_active=False)

        membership = cls.objects.create(
            user=user,
            plan=plan.value,
            start_date=now,
            end_date=end,
            is_active=True,
        )
        return membership

    def is_currently_valid(self) -> bool:
        if not self.is_active:
            return False
        return self.start_date <= timezone.now() <= self.end_date


class BookSection(models.Model):
    class Audience(models.TextChoices):
        KIDS = "KIDS", "Kids"
        ADULTS = "ADULTS", "Adults"
        GENERAL = "GENERAL", "General"

    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    audience = models.CharField(max_length=10, choices=Audience.choices, default=Audience.GENERAL)

    def __str__(self) -> str:
        return self.name


class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True)
    total_copies = models.PositiveIntegerField(default=1)
    sections = models.ManyToManyField(BookSection, related_name="books", blank=True)




    def __str__(self) -> str:
        return self.title

    @property
    def currently_available_copies(self) -> int:
        active_borrows = BorrowTransaction.objects.filter(book=self, is_returned=False).count()
        return max(self.total_copies - active_borrows, 0)


class BorrowTransaction(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="borrows")
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name="borrows")

    borrowed_at = models.DateTimeField(auto_now_add=True)
    due_at = models.DateTimeField()
    returned_at = models.DateTimeField(null=True, blank=True)

    is_returned = models.BooleanField(default=False)
    fine_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fine_paid = models.BooleanField(default=False)

    FINE_PER_DAY = 50

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_returned"]),
            models.Index(fields=["book", "is_returned"]),
        ]

    def __str__(self) -> str:
        return f"{self.user_id} -> {self.book_id}"

    def calculate_fine(self) -> "float":
        if self.is_returned and self.returned_at is not None:
            end_date = self.returned_at
        else:
            end_date = timezone.now()

        late_seconds = (end_date - self.due_at).total_seconds()
        if late_seconds <= 0:
            return 0

        late_days = int(late_seconds // 86400)  # floor by day
        # If they are late by any fraction of a day but within the same day window, treat as 0 by this rule.
        # For more strict behavior, use math.ceil.
        return float(late_days * self.FINE_PER_DAY)

    def return_book(self):
        if self.is_returned:
            return

        self.is_returned = True
        self.returned_at = timezone.now()
        # compute fine at return time
        self.fine_amount = self.calculate_fine()
        self.save(update_fields=["is_returned", "returned_at", "fine_amount"])

