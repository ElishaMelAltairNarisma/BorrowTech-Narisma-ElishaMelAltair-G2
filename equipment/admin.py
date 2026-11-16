from django.contrib import admin
from .models import Category, Equipment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'asset_code', 'category', 'available_quantity', 'total_quantity', 'condition', 'is_active')
    list_filter = ('category', 'condition', 'is_active')
    search_fields = ('name', 'asset_code', 'model_number')
    ordering = ('name',)
