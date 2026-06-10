from django.contrib import admin

from .models import Book, BorrowTransaction, Membership, BookSection



@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "plan", "start_date", "end_date", "is_active", "created_at"]
    list_filter = ["plan", "is_active"]
    search_fields = ["user__username"]


@admin.register(BookSection)
class BookSectionAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "slug", "audience"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "author", "total_copies"]
    search_fields = ["title", "author"]



@admin.register(BorrowTransaction)
class BorrowTransactionAdmin(admin.ModelAdmin):
    list_display = [
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
    list_filter = ["is_returned", "fine_paid"]
    search_fields = ["user__username", "book__title"]

