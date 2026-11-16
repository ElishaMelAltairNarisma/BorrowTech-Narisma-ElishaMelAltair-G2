from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds initial demo accounts for IT Student and Laboratory Custodian roles'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Seeding BorrowTech demo accounts...'))

        # 1. IT Student Account
        student, created = User.objects.get_or_create(
            username='it_student',
            defaults={
                'email': 'student@borrowtech.edu',
                'first_name': 'Juan',
                'last_name': 'Dela Cruz',
                'role': User.Role.STUDENT,
                'student_id': '2024-IT-0142',
                'department': 'College of Computer Studies (IT Dept)',
                'year_level': '3rd Year',
                'contact_number': '+63 917 123 4567',
            }
        )
        student.set_password('StudentPass2026!')
        student.save()
        if created:
            self.stdout.write(self.style.SUCCESS('  [+] Created demo IT Student account: it_student / StudentPass2026!'))
        else:
            self.stdout.write(self.style.WARNING('  [*] IT Student account already exists; password reset.'))

        # 2. Laboratory Custodian Account
        custodian, created = User.objects.get_or_create(
            username='lab_custodian',
            defaults={
                'email': 'custodian@borrowtech.edu',
                'first_name': 'Maria',
                'last_name': 'Santos',
                'role': User.Role.CUSTODIAN,
                'student_id': 'LAB-STAFF-01',
                'department': 'University IT Hardware Laboratory',
                'year_level': 'Faculty/Staff',
                'contact_number': '+63 918 987 6543',
                'is_staff': True,
            }
        )
        custodian.set_password('CustodianPass2026!')
        custodian.save()
        if created:
            self.stdout.write(self.style.SUCCESS('  [+] Created demo Custodian account: lab_custodian / CustodianPass2026!'))
        else:
            self.stdout.write(self.style.WARNING('  [*] Custodian account already exists; password reset.'))

        # 3. Superuser Account
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@borrowtech.edu',
                'first_name': 'System',
                'last_name': 'Administrator',
                'role': User.Role.CUSTODIAN,
                'student_id': 'SYS-ADMIN-01',
                'department': 'IT Infrastructure & Lab Systems',
                'year_level': 'Faculty/Staff',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        admin_user.set_password('AdminPass2026!')
        admin_user.save()
        if created:
            self.stdout.write(self.style.SUCCESS('  [+] Created Superuser admin account: admin / AdminPass2026!'))
        else:
            self.stdout.write(self.style.WARNING('  [*] Admin account already exists; password reset.'))

        self.stdout.write(self.style.SUCCESS('\nBorrowTech demo seeding completed successfully!'))
