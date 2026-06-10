from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .models import Book, BookSection, BorrowTransaction, Membership, MembershipPlan


def _has_active_membership(request) -> bool:
    if not request.user.is_authenticated:
        return False
    return Membership.objects.filter(
        user=request.user,
        is_active=True,
        start_date__lte=MembershipPlan,  # dummy to avoid template mistakes
    ).exists()


def home(request: HttpRequest) -> HttpResponse:
    has_membership = False
    if request.user.is_authenticated:
        # Use the model logic for correctness
        m = Membership.objects.filter(user=request.user).order_by("-created_at").first()
        has_membership = bool(m and m.is_currently_valid())

    return render(request, "library_app/home.html", {"has_membership": has_membership})


def sections(request: HttpRequest) -> HttpResponse:
    secs = BookSection.objects.all().annotate(books_count=Count("books")).order_by("name")
    return render(request, "library_app/sections.html", {"sections": secs})



def books_by_section(request: HttpRequest, slug: str) -> HttpResponse:
    section = get_object_or_404(BookSection, slug=slug)

    has_membership = False
    if request.user.is_authenticated:
        m = Membership.objects.filter(user=request.user).order_by("-created_at").first()
        has_membership = bool(m and m.is_currently_valid())

    books_qs = section.books.all().order_by("title")
    books = []
    for b in books_qs:
        books.append(
            {
                "id": b.id,
                "title": b.title,
                "author": b.author,
                "total_copies": b.total_copies,
                "available_copies": b.currently_available_copies,
            }
        )

    return render(
        request,
        "library_app/books_by_section.html",
        {
            "section": section,
            "books": books,
            "has_membership": has_membership,
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def membership(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        plan = request.POST.get("plan")
        try:
            plan_enum = MembershipPlan(plan)
        except ValueError:
            plan_enum = None

        if plan_enum is not None:
            Membership.create_for_user(request.user, plan_enum)
        return redirect("library-membership")

    m = Membership.objects.filter(user=request.user).order_by("-created_at").first()
    has_membership = bool(m and m.is_currently_valid())
    return render(request, "library_app/membership.html", {"has_membership": has_membership})


@login_required
@require_http_methods(["GET", "POST"])
def borrow(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        book_id = request.POST.get("book_id")
        book = get_object_or_404(Book, id=book_id)

        m = Membership.objects.filter(user=request.user).order_by("-created_at").first()
        if not (m and m.is_currently_valid()):
            return redirect("library-membership")

        if book.currently_available_copies <= 0:
            return redirect("library-books-by-section", book_id=book_id)

        from django.utils import timezone

        tx = BorrowTransaction.objects.create(
            user=request.user,
            book=book,
            due_at=timezone.now() + timezone.timedelta(days=30),
        )


        return redirect("library-my-transactions")

    return redirect("library-home")


@login_required
def my_transactions(request: HttpRequest) -> HttpResponse:
    txs = BorrowTransaction.objects.filter(user=request.user).select_related("book").order_by("-borrowed_at")
    return render(request, "library_app/my_transactions.html", {"transactions": txs})


@login_required
@require_http_methods(["POST"])
def return_borrow(request: HttpRequest) -> HttpResponse:
    borrow_id = request.POST.get("borrow_id")
    tx = get_object_or_404(BorrowTransaction, pk=borrow_id, user=request.user)
    if not tx.is_returned:
        tx.return_book()
    return redirect("library-my-transactions")

