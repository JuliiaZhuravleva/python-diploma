from django.core.management.base import BaseCommand
from backend.models import Category

class Command(BaseCommand):
    help = 'Creates a test category'

    def handle(self, *args, **options):
        category = Category.objects.create(name='Test Category')
        self.stdout.write(self.style.SUCCESS(f'Successfully created category: {category.name}'))