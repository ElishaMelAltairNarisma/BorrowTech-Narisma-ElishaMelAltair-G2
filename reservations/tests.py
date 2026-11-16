from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from equipment.models import Category, Equipment
from .models import BorrowReservation

User = get_user_model()


class BorrowReservationTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Users
        self.student1 = User.objects.create_user(
            username='student_juan',
            email='juan@university.edu',
            password='TestPassword123!',
            role=User.Role.STUDENT,
            first_name='Juan',
            last_name='Dela Cruz',
            student_id='2024-IT-0142'
        )
        self.student2 = User.objects.create_user(
            username='student_maria',
            email='maria@university.edu',
            password='TestPassword123!',
            role=User.Role.STUDENT,
            first_name='Maria',
            last_name='Clara',
            student_id='2024-IT-0999'
        )
        self.custodian = User.objects.create_user(
            username='custodian_staff',
            email='staff@university.edu',
            password='TestPassword123!',
            role=User.Role.CUSTODIAN,
            first_name='Lab',
            last_name='Custodian'
        )

        # Category and Equipment
        self.cat = Category.objects.create(name='IoT Kits', icon='fa-microchip')
        self.item = Equipment.objects.create(
            name='Arduino Uno Starter Kit',
            asset_code='EQ-ARD-999',
            category=self.cat,
            total_quantity=5,
            available_quantity=5,
            condition=Equipment.Condition.OPERATIONAL
        )

    def test_student_can_create_reservation(self):
        self.client.force_login(self.student1)
        today = timezone.now().date()
        data = {
            'equipment': self.item.id,
            'quantity': 2,
            'start_date': today,
            'expected_return_date': today + timedelta(days=3),
            'purpose': 'CSIT327 Lab Practical #1',
        }
        response = self.client.post(reverse('reservation_create'), data)
        created = BorrowReservation.objects.filter(borrower=self.student1).first()
        self.assertIsNotNone(created)
        self.assertEqual(created.status, BorrowReservation.Status.PENDING)
        self.assertEqual(created.quantity, 2)
        self.assertRedirects(response, reverse('reservation_detail', kwargs={'pk': created.pk}))

    def test_reservation_stock_validation(self):
        """Cannot request more than available equipment units."""
        self.client.force_login(self.student1)
        today = timezone.now().date()
        data = {
            'equipment': self.item.id,
            'quantity': 10,  # Only 5 available!
            'start_date': today,
            'expected_return_date': today + timedelta(days=2),
            'purpose': 'Invalid stock request',
        }
        response = self.client.post(reverse('reservation_create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'quantity', 'Requested quantity (10) exceeds available stock (5 unit(s)).')

    def test_reservation_max_7_days_validation(self):
        """Borrowing duration cannot exceed 7 calendar days."""
        self.client.force_login(self.student1)
        today = timezone.now().date()
        data = {
            'equipment': self.item.id,
            'quantity': 1,
            'start_date': today,
            'expected_return_date': today + timedelta(days=14),  # Exceeds 7 days!
            'purpose': 'Too long loan request',
        }
        response = self.client.post(reverse('reservation_create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'expected_return_date', 'Borrowing period cannot exceed the 7-day maximum laboratory loan policy.')

    def test_reservation_quota_limit_3_items(self):
        """Student cannot have more than 3 active or pending reservations concurrently."""
        today = timezone.now().date()
        for i in range(3):
            BorrowReservation.objects.create(
                borrower=self.student1,
                equipment=self.item,
                quantity=1,
                purpose=f'Active loan {i}',
                start_date=today,
                expected_return_date=today + timedelta(days=2),
                status=BorrowReservation.Status.PENDING
            )

        self.client.force_login(self.student1)
        data = {
            'equipment': self.item.id,
            'quantity': 1,
            'start_date': today,
            'expected_return_date': today + timedelta(days=2),
            'purpose': '4th attempt',
        }
        response = self.client.post(reverse('reservation_create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Quota limit reached' in str(response.context['form'].non_field_errors()))

    def test_student_cannot_view_other_student_reservation(self):
        """Privacy: Student 2 cannot access Student 1's digital pass."""
        today = timezone.now().date()
        res = BorrowReservation.objects.create(
            borrower=self.student1,
            equipment=self.item,
            quantity=1,
            purpose='Juan private request',
            start_date=today,
            expected_return_date=today + timedelta(days=2)
        )
        self.client.force_login(self.student2)
        response = self.client.get(reverse('reservation_detail', kwargs={'pk': res.pk}))
        # Denied and redirected to Student 2's own reservations
        self.assertRedirects(response, reverse('my_reservations'))

    def test_student_can_update_pending_reservation(self):
        today = timezone.now().date()
        res = BorrowReservation.objects.create(
            borrower=self.student1,
            equipment=self.item,
            quantity=1,
            purpose='Original purpose',
            start_date=today,
            expected_return_date=today + timedelta(days=2),
            status=BorrowReservation.Status.PENDING
        )
        self.client.force_login(self.student1)
        data = {
            'quantity': 2,
            'expected_return_date': today + timedelta(days=4),
            'purpose': 'Updated purpose for project',
        }
        response = self.client.post(reverse('reservation_update', kwargs={'pk': res.pk}), data)
        self.assertRedirects(response, reverse('reservation_detail', kwargs={'pk': res.pk}))
        res.refresh_from_db()
        self.assertEqual(res.quantity, 2)
        self.assertEqual(res.purpose, 'Updated purpose for project')

    def test_student_can_cancel_reservation(self):
        today = timezone.now().date()
        res = BorrowReservation.objects.create(
            borrower=self.student1,
            equipment=self.item,
            quantity=1,
            purpose='To be cancelled',
            start_date=today,
            expected_return_date=today + timedelta(days=2),
            status=BorrowReservation.Status.PENDING
        )
        self.client.force_login(self.student1)
        response = self.client.post(reverse('reservation_cancel', kwargs={'pk': res.pk}))
        self.assertRedirects(response, reverse('my_reservations'))
        res.refresh_from_db()
        self.assertEqual(res.status, BorrowReservation.Status.CANCELLED)

    def test_custodian_approval_and_issue_workflow(self):
        """Full end-to-end approval, handover, stock deduction, and return flow."""
        today = timezone.now().date()
        res = BorrowReservation.objects.create(
            borrower=self.student1,
            equipment=self.item,
            quantity=2,
            purpose='Hardware Testing Session',
            start_date=today,
            expected_return_date=today + timedelta(days=2),
            status=BorrowReservation.Status.PENDING
        )

        self.client.force_login(self.custodian)

        # 1. Approve
        response = self.client.get(reverse('custodian_approve', kwargs={'pk': res.pk}))
        self.assertRedirects(response, reverse('custodian_queue'))
        res.refresh_from_db()
        self.assertEqual(res.status, BorrowReservation.Status.APPROVED)

        # 2. Handover / Issue (deducts stock)
        initial_stock = self.item.available_quantity
        response = self.client.get(reverse('custodian_issue', kwargs={'pk': res.pk}))
        self.assertRedirects(response, reverse('custodian_queue'))
        res.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(res.status, BorrowReservation.Status.ISSUED)
        self.assertEqual(self.item.available_quantity, initial_stock - 2)

        # 3. Process Return (restores stock)
        return_data = {
            'return_condition': BorrowReservation.Condition.OPERATIONAL,
            'custodian_remarks': 'All parts verified intact by lab technician.',
        }
        response = self.client.post(reverse('custodian_return', kwargs={'pk': res.pk}), return_data)
        self.assertRedirects(response, reverse('custodian_queue'))
        res.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(res.status, BorrowReservation.Status.RETURNED)
        self.assertEqual(res.return_condition, BorrowReservation.Condition.OPERATIONAL)
        self.assertEqual(self.item.available_quantity, initial_stock)
        self.assertEqual(res.inspected_by, self.custodian)
        self.assertIsNotNone(res.actual_return_date)
