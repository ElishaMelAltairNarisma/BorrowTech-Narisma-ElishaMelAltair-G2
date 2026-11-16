from django.db import models
from django.conf import settings
from django.utils import timezone
import random


class BorrowReservation(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Custodian Approval'
        APPROVED = 'APPROVED', 'Approved (Ready for Handover)'
        ISSUED = 'ISSUED', 'Active Loan (Checked Out)'
        RETURNED = 'RETURNED', 'Returned & Inspected'
        REJECTED = 'REJECTED', 'Reservation Rejected'
        CANCELLED = 'CANCELLED', 'Cancelled by Student'

    class Condition(models.TextChoices):
        OPERATIONAL = 'OPERATIONAL', 'Operational (Complete & Functional)'
        DAMAGED = 'DAMAGED', 'Damaged / Hardware Defect'
        INCOMPLETE = 'INCOMPLETE', 'Missing Components / Accessories'

    # Integration with Account Feature (User ForeignKey)
    borrower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='borrow_reservations',
        verbose_name='Student Borrower'
    )
    # Relationship to Equipment
    equipment = models.ForeignKey(
        'equipment.Equipment',
        on_delete=models.PROTECT,
        related_name='reservations',
        verbose_name='Laboratory Equipment'
    )

    reservation_code = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        verbose_name='Reservation Tracking Code'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        help_text='Number of units requested (subject to stock availability)'
    )
    purpose = models.TextField(
        verbose_name='Academic Purpose',
        help_text='Course code, experiment title, capstone, or practical exam details'
    )
    start_date = models.DateField(
        default=timezone.now,
        verbose_name='Reservation Date'
    )
    expected_return_date = models.DateField(
        verbose_name='Expected Return Date',
        help_text='Maximum 7 calendar days allowed per university laboratory policy'
    )
    actual_return_date = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Actual Return Timestamp'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    custodian_remarks = models.TextField(
        blank=True,
        null=True,
        verbose_name='Custodian Remarks / Notes'
    )
    inspected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='inspected_loans',
        verbose_name='Inspected by Lab Custodian'
    )
    return_condition = models.CharField(
        max_length=20,
        choices=Condition.choices,
        blank=True,
        null=True,
        verbose_name='Return Condition'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Borrowing Reservation'
        verbose_name_plural = 'Borrowing Reservations'

    def save(self, *args, **kwargs):
        if not self.reservation_code:
            year = timezone.now().year
            rand_suffix = random.randint(1000, 9999)
            self.reservation_code = f"RES-{year}-{rand_suffix}"
            while BorrowReservation.objects.filter(reservation_code=self.reservation_code).exists():
                rand_suffix = random.randint(1000, 9999)
                self.reservation_code = f"RES-{year}-{rand_suffix}"
        super().save(*args, **kwargs)

    @property
    def is_overdue(self):
        if self.status == self.Status.ISSUED and self.expected_return_date:
            return timezone.now().date() > self.expected_return_date
        return False

    @property
    def can_edit(self):
        """Student can only edit their reservation while it is still pending."""
        return self.status == self.Status.PENDING

    @property
    def can_cancel(self):
        """Student can cancel reservation if not yet issued into circulation."""
        return self.status in [self.Status.PENDING, self.Status.APPROVED]

    @property
    def status_badge(self):
        badges = {
            self.Status.PENDING: {'text': 'Pending Approval', 'color': 'amber', 'bg': 'bg-amber-50', 'text_color': 'text-amber-700', 'border': 'border-amber-200'},
            self.Status.APPROVED: {'text': 'Approved (Ready)', 'color': 'blue', 'bg': 'bg-blue-50', 'text_color': 'text-blue-700', 'border': 'border-blue-200'},
            self.Status.ISSUED: {'text': 'Active Loan (Checked Out)', 'color': 'purple', 'bg': 'bg-purple-50', 'text_color': 'text-purple-700', 'border': 'border-purple-200'},
            self.Status.RETURNED: {'text': 'Returned & Inspected', 'color': 'emerald', 'bg': 'bg-emerald-50', 'text_color': 'text-emerald-700', 'border': 'border-emerald-200'},
            self.Status.REJECTED: {'text': 'Request Rejected', 'color': 'rose', 'bg': 'bg-rose-50', 'text_color': 'text-rose-700', 'border': 'border-rose-200'},
            self.Status.CANCELLED: {'text': 'Cancelled by User', 'color': 'slate', 'bg': 'bg-slate-100', 'text_color': 'text-slate-600', 'border': 'border-slate-300'},
        }
        if self.is_overdue:
            return {'text': 'OVERDUE RETURN', 'color': 'red', 'bg': 'bg-red-100', 'text_color': 'text-red-800', 'border': 'border-red-400'}
        return badges.get(self.status, {'text': self.get_status_display(), 'color': 'slate', 'bg': 'bg-slate-100', 'text_color': 'text-slate-600', 'border': 'border-slate-300'})

    def __str__(self):
        return f"{self.reservation_code} - {self.equipment.name} ({self.borrower.username})"
