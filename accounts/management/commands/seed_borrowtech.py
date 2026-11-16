from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from equipment.models import Category, Equipment

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds initial demo accounts and laboratory equipment inventory'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Seeding BorrowTech demo accounts & laboratory inventory...'))

        # 1. Accounts
        student, _ = User.objects.get_or_create(
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

        custodian, _ = User.objects.get_or_create(
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

        admin_user, _ = User.objects.get_or_create(
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

        # 2. Categories
        cat_iot, _ = Category.objects.get_or_create(
            name='Embedded Systems & IoT',
            defaults={'icon': 'fa-microchip', 'description': 'Microcontroller kits, sensors, and actuator modules for embedded software development.'}
        )
        cat_net, _ = Category.objects.get_or_create(
            name='Networking & Communications',
            defaults={'icon': 'fa-network-wired', 'description': 'Routers, manageable switches, patch panels, and networking crimp tools.'}
        )
        cat_test, _ = Category.objects.get_or_create(
            name='Testing & Measurement',
            defaults={'icon': 'fa-plug', 'description': 'Digital multimeters, oscilloscopes, DC power supplies, and function generators.'}
        )
        cat_sbc, _ = Category.objects.get_or_create(
            name='Single Board Computers',
            defaults={'icon': 'fa-server', 'description': 'Raspberry Pi units, compute modules, and AI edge accelerators.'}
        )
        cat_proto, _ = Category.objects.get_or_create(
            name='Prototyping & Soldering',
            defaults={'icon': 'fa-fire-burner', 'description': 'Soldering stations, de-soldering pumps, helping hands, and breadboards.'}
        )

        # 3. Equipment Items
        items_data = [
            {
                'name': 'Arduino Uno R3 Starter Kit',
                'asset_code': 'EQ-ARD-010',
                'category': cat_iot,
                'model_number': 'A000066',
                'description': 'Full microcontroller kit with ATmega328P, breadboard, 65 jumper wires, LEDs, resistors, and USB interface cable.',
                'total_quantity': 15,
                'available_quantity': 12,
                'laboratory_room': 'Room 402 - IoT & Embedded Lab',
                'storage_location': 'Cabinet A - Shelf 2',
                'condition': Equipment.Condition.OPERATIONAL,
            },
            {
                'name': 'Raspberry Pi 4 Model B (8GB RAM)',
                'asset_code': 'EQ-RPI-024',
                'category': cat_sbc,
                'model_number': 'RPI4-MODBP-8GB',
                'description': 'Quad-core 64-bit Cortex-A72 processor, dual micro-HDMI 4K outputs, Gigabit Ethernet, 32GB microSD preloaded with Raspberry Pi OS.',
                'total_quantity': 8,
                'available_quantity': 4,
                'laboratory_room': 'Room 402 - IoT & Embedded Lab',
                'storage_location': 'Cabinet B - Shelf 1',
                'condition': Equipment.Condition.OPERATIONAL,
            },
            {
                'name': 'Fluke 87V Industrial Digital Multimeter',
                'asset_code': 'EQ-FLK-003',
                'category': cat_test,
                'model_number': 'FLUKE-87-5',
                'description': 'True-RMS industrial multimeter with temperature probe, silicone test leads, alligator clips, and protective holster.',
                'total_quantity': 6,
                'available_quantity': 6,
                'laboratory_room': 'Room 403 - Hardware Diagnostics Lab',
                'storage_location': 'Cabinet C - Shelf 3',
                'condition': Equipment.Condition.OPERATIONAL,
            },
            {
                'name': 'Cisco Catalyst 2960-X 24-Port Switch',
                'asset_code': 'EQ-NET-015',
                'category': cat_net,
                'model_number': 'WS-C2960X-24TS-L',
                'description': 'Enterprise Gigabit Ethernet managed switch, console rollover cable, and power lead for CCNA laboratory practicals.',
                'total_quantity': 4,
                'available_quantity': 1,
                'laboratory_room': 'Room 405 - Networking & Telecomm Lab',
                'storage_location': 'Rack B - Slot 04',
                'condition': Equipment.Condition.OPERATIONAL,
            },
            {
                'name': 'Rigol DS1054Z Digital Oscilloscope (50MHz)',
                'asset_code': 'EQ-OSC-007',
                'category': cat_test,
                'model_number': 'DS1054Z',
                'description': '4-channel digital storage oscilloscope with 1 GSa/s real-time sample rate, 4 passive probes, and USB connectivity.',
                'total_quantity': 5,
                'available_quantity': 3,
                'laboratory_room': 'Room 403 - Hardware Diagnostics Lab',
                'storage_location': 'Bench 4 - Equipment Station',
                'condition': Equipment.Condition.OPERATIONAL,
            },
            {
                'name': 'Weller WE1010 Digital Soldering Station',
                'asset_code': 'EQ-SOL-004',
                'category': cat_proto,
                'model_number': 'WE1010NA',
                'description': '70W digital soldering station with heat-resistant silicone cord, safety rest, cleaning sponge, and fine conical tip.',
                'total_quantity': 10,
                'available_quantity': 8,
                'laboratory_room': 'Room 401 - Circuit Fabrication Lab',
                'storage_location': 'Soldering Bay A',
                'condition': Equipment.Condition.OPERATIONAL,
            },
        ]

        for item_data in items_data:
            code = item_data['asset_code']
            item, created = Equipment.objects.get_or_create(
                asset_code=code,
                defaults=item_data
            )
            if not created:
                for key, val in item_data.items():
                    setattr(item, key, val)
                item.save()

        self.stdout.write(self.style.SUCCESS('Successfully seeded categories, equipment items, and user accounts!'))
