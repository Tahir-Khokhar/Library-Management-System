from django.core.management.base import BaseCommand
from django.db import transaction

from library_app.models import Book, BookSection


class Command(BaseCommand):
    help = "Seed sample library sections and books (idempotent)."

    def handle(self, *args, **options):
        with transaction.atomic():
            sections = [
                # Kids
                ("Kids - Story Books", "kids-stories", BookSection.Audience.KIDS),
                ("Kids - Comics", "kids-comics", BookSection.Audience.KIDS),
                ("Kids - Manga", "kids-manga", BookSection.Audience.KIDS),
                # Adults
                ("Adults - Newspaper Collection (Whole Year)", "adults-newspapers", BookSection.Audience.ADULTS),
                # General / Pakistan library-style examples
                ("Pakistan - History & Biography", "pak-history", BookSection.Audience.GENERAL),
                ("Pakistan - Poetry", "pak-poetry", BookSection.Audience.GENERAL),
                ("Pakistan - Religion & Islamic Studies", "pak-islamic-studies", BookSection.Audience.GENERAL),
                ("Pakistan - Language & Literature", "pak-language-literature", BookSection.Audience.GENERAL),
                ("Pakistan - Science & Technology", "pak-science-tech", BookSection.Audience.GENERAL),
                ("Pakistan - Sports & Arts", "pak-sports-arts", BookSection.Audience.GENERAL),
            ]

            section_objs_by_slug = {}
            for name, slug, audience in sections:
                section_obj, _ = BookSection.objects.get_or_create(
                    slug=slug,
                    defaults={"name": name, "audience": audience},
                )
                # Keep fields in sync if changed
                if section_obj.name != name or section_obj.audience != audience:
                    section_obj.name = name
                    section_obj.audience = audience
                    section_obj.save(update_fields=["name", "audience"])

                section_objs_by_slug[slug] = section_obj

            # Sample books only (safe starter dataset)
            sample_books = [
                # Kids stories
                ("Sample Kids Story Book - Dawn of Knowledge", "Unknown Muslim Author", "kids-stories"),
                ("Sample Kids Story Book - River of Kindness", "Unknown Muslim Author", "kids-stories"),
                # Kids comics/manga
                ("Sample Kids Comic - Brave Hearts", "Unknown", "kids-comics"),
                ("Sample Kids Manga - Starry Nights", "Unknown", "kids-manga"),
                # Adults newspapers
                ("Sample Adult Newspaper Collection - Year 20XX (Placeholder)", "Library Archive", "adults-newspapers"),
                # General Pakistan-style
                ("Sample Biography - Makers of the Nation (Placeholder)", "Unknown", "pak-history"),
                ("Sample Poetry Collection - Verses of Peace (Placeholder)", "Unknown", "pak-poetry"),
                ("Sample Islamic Studies Text - Foundations (Placeholder)", "Unknown", "pak-islamic-studies"),
                ("Sample Literature - Stories of Language (Placeholder)", "Unknown", "pak-language-literature"),
                ("Sample Science & Technology - Tools of Tomorrow (Placeholder)", "Unknown", "pak-science-tech"),
            ]

            for title, author, section_slug in sample_books:
                section = section_objs_by_slug[section_slug]
                book, _ = Book.objects.get_or_create(
                    title=title,
                    author=author,
                    defaults={"total_copies": 3},
                )
                # Attach section if not attached
                if not book.sections.filter(id=section.id).exists():
                    book.sections.add(section)

        self.stdout.write(self.style.SUCCESS("Seed completed successfully."))

