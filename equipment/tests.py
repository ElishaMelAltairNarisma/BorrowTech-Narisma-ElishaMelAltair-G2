from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Category, Equipment

User = get_user_model()


class EquipmentModelTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name='Embedded Systems & IoT',
            icon='fa-microchip',
            description='Microcontroller development kits'
        )
        self.equipment = Equipment.objects.create(
            name='Arduino Uno R3',
            asset_code='EQ-ARD-001',
            category=self.category,
            total_quantity=10,
            available_quantity=8,
            laboratory_room='Room 402',
            storage_location='Cabinet A',
            condition=Equipment.Condition.OPERATIONAL
        )

    def test_category_slug_auto_generated(self):
        self.assertEqual(self.category.slug, 'embedded-systems-iot')

    def test_equipment_availability_property(self):
        self.assertTrue(self.equipment.is_available)
        self.equipment.available_quantity = 0
        self.assertFalse(self.equipment.is_available)

    def test_status_display(self):
        self.equipment.available_quantity = 5
        self.assertEqual(self.equipment.status_display['color'], 'emerald')
        self.equipment.available_quantity = 1
        self.assertEqual(self.equipment.status_display['color'], 'amber')
        self.equipment.available_quantity = 0
        self.assertEqual(self.equipment.status_display['color'], 'rose')


class EquipmentViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            username='student_test',
            email='student_test@univ.edu',
            password='TestPassword123!',
            role=User.Role.STUDENT
        )
        self.custodian = User.objects.create_user(
            username='custodian_test',
            email='custodian_test@univ.edu',
            password='TestPassword123!',
            role=User.Role.CUSTODIAN
        )
        self.category = Category.objects.create(name='Networking Gear', icon='fa-network-wired')
        self.item = Equipment.objects.create(
            name='Cisco Catalyst Switch 2960',
            asset_code='EQ-NET-001',
            category=self.category,
            total_quantity=4,
            available_quantity=4,
            description='24-port Gigabit managed switch'
        )

    def test_equipment_list_requires_login(self):
        response = self.client.get(reverse('equipment_list'))
        self.assertEqual(response.status_code, 302)

    def test_student_can_view_equipment_list_and_search(self):
        self.client.force_login(self.student)
        response = self.client.get(reverse('equipment_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Cisco Catalyst Switch 2960')

        # Test search query
        response = self.client.get(reverse('equipment_list') + '?q=Cisco')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'EQ-NET-001')

    def test_student_cannot_create_equipment(self):
        """Students must not be able to create new equipment records."""
        self.client.force_login(self.student)
        response = self.client.get(reverse('equipment_create'))
        # Blocked and redirected to student dashboard
        self.assertRedirects(response, reverse('student_dashboard'))

    def test_custodian_can_create_equipment(self):
        self.client.force_login(self.custodian)
        data = {
            'name': 'Raspberry Pi 4 Model B',
            'asset_code': 'EQ-RPI-002',
            'category': self.category.id,
            'description': '8GB RAM single-board computer for IoT projects',
            'total_quantity': 5,
            'available_quantity': 5,
            'laboratory_room': 'Room 402',
            'storage_location': 'Cabinet B - Shelf 1',
            'condition': Equipment.Condition.OPERATIONAL,
            'is_active': True,
        }
        response = self.client.post(reverse('equipment_create'), data)
        created = Equipment.objects.filter(asset_code='EQ-RPI-002').first()
        self.assertIsNotNone(created)
        self.assertRedirects(response, reverse('equipment_detail', kwargs={'pk': created.pk}))

    def test_custodian_can_update_equipment(self):
        self.client.force_login(self.custodian)
        data = {
            'name': 'Cisco Catalyst Switch 2960-X (Updated)',
            'asset_code': 'EQ-NET-001',
            'category': self.category.id,
            'description': 'Updated switch specifications',
            'total_quantity': 6,
            'available_quantity': 6,
            'laboratory_room': 'Room 403',
            'storage_location': 'Rack 2',
            'condition': Equipment.Condition.OPERATIONAL,
            'is_active': True,
        }
        response = self.client.post(reverse('equipment_update', kwargs={'pk': self.item.pk}), data)
        self.assertRedirects(response, reverse('equipment_detail', kwargs={'pk': self.item.pk}))
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, 'Cisco Catalyst Switch 2960-X (Updated)')
        self.assertEqual(self.item.total_quantity, 6)

    def test_custodian_can_delete_equipment(self):
        self.client.force_login(self.custodian)
        response = self.client.post(reverse('equipment_delete', kwargs={'pk': self.item.pk}))
        self.assertRedirects(response, reverse('equipment_list'))
        self.assertFalse(Equipment.objects.filter(pk=self.item.pk).exists())
