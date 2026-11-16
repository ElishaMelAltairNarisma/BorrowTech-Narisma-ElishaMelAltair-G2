from django.contrib import admin
from .models import BorrowReservation


@admin.register(BorrowReservation)
class BorrowReservationAdmin(admin.ModelAdmin):
    list_display = (
        'reservation_code',
        'borrower',
        'equipment',
        'quantity',
        'start_date',
        'expected_return_date',
        'status',
        'is_overdue_display'
    )
    list_filter = ('status', 'start_date', 'expected_return_date', 'return_condition')
    search_fields = (
        'reservation_code',
        'borrower__username',
        'borrower__student_id',
        'equipment__name',
        'equipment__asset_code'
    )
    ordering = ('-created_at',)

    @admin.display(boolean=True, description='Overdue?')
    def is_overdue_display(self, obj):
        return obj.is_overdue
