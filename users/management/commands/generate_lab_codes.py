from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from users.models import LabAttendantRegistrationCode, User

class Command(BaseCommand):
    help = 'Generate lab attendant registration codes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='Number of codes to generate (default: 5)'
        )
        parser.add_argument(
            '--admin-user',
            type=str,
            help='Username of admin user to create codes (default: first admin user)'
        )
        parser.add_argument(
            '--email',
            type=str,
            required=True,
            help='Email address for the registration code'
        )

    def handle(self, *args, **options):
        count = options['count']
        admin_username = options['admin_user']
        email = options['email']
        
        # Get admin user
        if admin_username:
            try:
                admin_user = User.objects.get(username=admin_username, role=User.Role.ADMIN)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Admin user "{admin_username}" not found or not an admin.')
                )
                return
        else:
            admin_user = User.objects.filter(role=User.Role.ADMIN).first()
            if not admin_user:
                self.stdout.write(
                    self.style.ERROR('No admin user found. Please create an admin user first.')
                )
                return
        
        # Generate codes
        generated_codes = []
        for i in range(count):
            code = get_random_string(8).upper()
            registration_code = LabAttendantRegistrationCode.objects.create(
                email=email,
                code=code,
                created_by=admin_user,
                notes=f"Auto-generated code #{i+1}"
            )
            generated_codes.append(code)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully generated {count} lab attendant registration codes:')
        )
        for code in generated_codes:
            self.stdout.write(f'  - {code}')
        
        self.stdout.write(
            self.style.WARNING(
                '\nShare these codes with lab attendants who need to register. '
                'Each code can only be used once.'
            )
        ) 