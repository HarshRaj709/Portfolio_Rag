from django.core.management.base import BaseCommand
from portfolio_rag_bot.rag_pipeline import SupabaseRAG
import os
from django.conf import settings


class Command(BaseCommand):
    def handle(self, *args, **options):
        file_path = os.path.join(settings.BASE_DIR, 'personal_info.md')
        SupabaseRAG().ingest(file_path)
        self.stdout.write("Done!")
