from django.urls import path

from .views import BookViewSet, BorrowViewSet, MembershipViewSet, MyTransactionsViewSet, ReturnBorrowViewSet
from .views_web import (
    borrow,
    books_by_section,
    home,
    membership,
    my_transactions,
    return_borrow,
    sections,
)

membership_list = MembershipViewSet.as_view({"get": "list", "post": "create"})

urlpatterns = [
    # HTML pages (Django templates)
    path("", home, name="library-home"),
    path("sections/", sections, name="library-sections"),
    path("sections/<slug:slug>/books/", books_by_section, name="library-books-by-section"),
    path("membership/", membership, name="library-membership"),
    path("my-transactions/", my_transactions, name="library-my-transactions"),
    path("return-borrow/", return_borrow, name="library-return-borrow"),
    path("borrow/", borrow, name="library-borrow"),

    # DRF API endpoints
    path("api/membership/", membership_list, name="membership"),
    path("api/books/", BookViewSet.as_view({"get": "list"}), name="books"),
    path("api/borrows/", BorrowViewSet.as_view({"post": "create"}), name="borrow"),
    path("api/borrows/<int:pk>/", BorrowViewSet.as_view({"get": "retrieve"}), name="borrow-detail"),
    path("api/return-borrow/", ReturnBorrowViewSet.as_view({"post": "create"}), name="return-borrow"),
    path("api/my-transactions/", MyTransactionsViewSet.as_view({"get": "list"}), name="my-transactions"),
]



