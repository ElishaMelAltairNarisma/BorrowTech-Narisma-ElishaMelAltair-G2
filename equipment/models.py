from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50,
        default='fa-microchip',
        help_text='FontAwesome icon class (e.g., fa-microchip, fa-network-wired, fa-plug)'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Equipment(models.Model):
    class Condition(models.TextChoices):
        OPERATIONAL = 'Operational', 'Operational (Fully Functional)'
        NEEDS_MAINTENANCE = 'Needs Maintenance', 'Needs Maintenance'
        UNDER_REPAIR = 'Under Repair', 'Under Repair'
        RETIRED = 'Retired', 'Retired / Decommissioned'

    name = models.CharField(max_length=150, verbose_name='Equipment Name')
    asset_code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Asset / Barcode Number',
        help_text='Unique institutional asset code (e.g., EQ-ARD-010)'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='equipment_items'
    )
    model_number = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(help_text='Detailed specifications and included accessories')
    total_quantity = models.PositiveIntegerField(default=1, verbose_name='Total Inventory Units')
    available_quantity = models.PositiveIntegerField(default=1, verbose_name='Available Units for Borrowing')
    laboratory_room = models.CharField(
        max_length=100,
        default='Room 402 - IT Hardware Laboratory',
        help_text='Designated laboratory room'
    )
    storage_location = models.CharField(
        max_length=100,
        default='Cabinet A - Shelf 1',
        help_text='Specific storage shelf, locker, or bench'
    )
    condition = models.CharField(
        max_length=30,
        choices=Condition.choices,
        default=Condition.OPERATIONAL
    )
    image = models.ImageField(upload_to='equipment_images/', blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text='Available for public browsing and borrowing')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Laboratory Equipment'
        verbose_name_plural = 'Laboratory Equipment'
        ordering = ['name']

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.available_quantity > self.total_quantity:
            raise ValidationError({
                'available_quantity': 'Available units cannot exceed total inventory units.'
            })

    @property
    def is_available(self):
        return self.available_quantity > 0 and self.condition == self.Condition.OPERATIONAL and self.is_active

    @property
    def status_display(self):
        if not self.is_active or self.condition != self.Condition.OPERATIONAL:
            return {'text': self.get_condition_display(), 'color': 'red'}
        if self.available_quantity == 0:
            return {'text': 'Checked Out', 'color': 'rose'}
        if self.available_quantity <= 2:
            return {'text': f'Limited ({self.available_quantity} left)', 'color': 'amber'}
        return {'text': f'{self.available_quantity} Available', 'color': 'emerald'}

    def __str__(self):
        return f"{self.name} ({self.asset_code})"
