from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta

from equipment.models import Equipment
from .models import BorrowReservation


class BorrowReservationCreateForm(forms.ModelForm):
    class Meta:
        model = BorrowReservation
        fields = [
            'equipment',
            'quantity',
            'start_date',
            'expected_return_date',
            'purpose',
        ]
        widgets = {
            'equipment': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none transition'
            }),
            'quantity': forms.NumberInput(attrs={
                'min': 1,
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none transition'
            }),
            'start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none transition'
            }),
            'expected_return_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none transition'
            }),
            'purpose': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Specify course code, laboratory experiment title, group members, or capstone hardware scope...',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none transition'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Filter equipment to only active items with stock available
        self.fields['equipment'].queryset = Equipment.objects.filter(
            is_active=True,
            condition=Equipment.Condition.OPERATIONAL
        )
        # Default start date to today and return date to 2 days from today
        today = timezone.now().date()
        self.fields['start_date'].initial = today
        self.fields['expected_return_date'].initial = today + timedelta(days=2)

    def clean(self):
        cleaned_data = super().clean()
        equipment = cleaned_data.get('equipment')
        quantity = cleaned_data.get('quantity')
        start_date = cleaned_data.get('start_date')
        expected_return_date = cleaned_data.get('expected_return_date')

        today = timezone.now().date()

        # Business Rule 1: Student concurrent loan quota limit (Max 3 items)
        if self.user:
            active_count = BorrowReservation.objects.filter(
                borrower=self.user,
                status__in=[
                    BorrowReservation.Status.PENDING,
                    BorrowReservation.Status.APPROVED,
                    BorrowReservation.Status.ISSUED,
                ]
            ).count()
            if active_count >= 3:
                raise ValidationError(
                    "Quota limit reached: You have 3 concurrent active or pending equipment reservations. "
                    "Please return or complete existing reservations before requesting more hardware."
                )

        # Business Rule 2: Stock availability check
        if equipment and quantity:
            if quantity > equipment.available_quantity:
                self.add_error(
                    'quantity',
                    f"Requested quantity ({quantity}) exceeds available stock ({equipment.available_quantity} unit(s))."
                )

        # Business Rule 3: Start Date cannot be in the past
        if start_date and start_date < today:
            self.add_error('start_date', 'Reservation start date cannot be in the past.')

        # Business Rule 4: Return date validation
        if start_date and expected_return_date:
            if expected_return_date < start_date:
                self.add_error(
                    'expected_return_date',
                    'Expected return date cannot precede the reservation start date.'
                )
            elif (expected_return_date - start_date).days > 7:
                self.add_error(
                    'expected_return_date',
                    'Borrowing period cannot exceed the 7-day maximum laboratory loan policy.'
                )

        return cleaned_data


class BorrowReservationUpdateForm(forms.ModelForm):
    class Meta:
        model = BorrowReservation
        fields = [
            'quantity',
            'expected_return_date',
            'purpose',
        ]
        widgets = {
            'quantity': forms.NumberInput(attrs={
                'min': 1,
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none transition'
            }),
            'expected_return_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none transition'
            }),
            'purpose': forms.Textarea(attrs={
                'rows': 3,
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none transition'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        expected_return_date = cleaned_data.get('expected_return_date')

        if self.instance and self.instance.equipment:
            if quantity and quantity > self.instance.equipment.available_quantity:
                self.add_error(
                    'quantity',
                    f"Quantity cannot exceed available units ({self.instance.equipment.available_quantity})."
                )

        if expected_return_date and self.instance.start_date:
            if expected_return_date < self.instance.start_date:
                self.add_error('expected_return_date', 'Return date cannot precede reservation date.')
            elif (expected_return_date - self.instance.start_date).days > 7:
                self.add_error('expected_return_date', 'Borrowing duration cannot exceed 7 days.')

        return cleaned_data


class CustodianReturnForm(forms.Form):
    return_condition = forms.ChoiceField(
        label='Hardware Condition Inspection',
        choices=BorrowReservation.Condition.choices,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none transition'
        })
    )
    custodian_remarks = forms.CharField(
        label='Inspection Remarks / Component Audit',
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Confirm all cables, sensors, and protective cases are accounted for. Note any cosmetic wear or hardware issues...',
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none transition'
        })
    )


class CustodianRejectForm(forms.Form):
    custodian_remarks = forms.CharField(
        label='Reason for Rejection',
        required=True,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'State clearly why this reservation is rejected (e.g., equipment reserved for class examination, invalid course justification)...',
            'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-rose-500 focus:outline-none transition'
        })
    )
