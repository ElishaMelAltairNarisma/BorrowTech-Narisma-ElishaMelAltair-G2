from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q

from accounts.decorators import custodian_required
from .models import Equipment, Category
from .forms import EquipmentForm, EquipmentFilterForm


@login_required
def equipment_list_view(request):
    """
    Catalog Browsing (Read operation):
    - Available to all authenticated students and custodians.
    - Live search by keyword and category filtering.
    - Status pills indicating availability.
    """
    equipment_qs = Equipment.objects.filter(is_active=True).select_related('category')
    filter_form = EquipmentFilterForm(request.GET)

    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    availability = request.GET.get('availability')

    if query:
        equipment_qs = equipment_qs.filter(
            Q(name__icontains=query) |
            Q(asset_code__icontains=query) |
            Q(model_number__icontains=query) |
            Q(description__icontains=query)
        )

    if category_id:
        equipment_qs = equipment_qs.filter(category_id=category_id)

    if availability == 'available':
        equipment_qs = equipment_qs.filter(available_quantity__gt=0, condition=Equipment.Condition.OPERATIONAL)
    elif availability == 'limited':
        equipment_qs = equipment_qs.filter(available_quantity__gt=0, available_quantity__lte=2)
    elif availability == 'checked_out':
        equipment_qs = equipment_qs.filter(available_quantity=0)

    categories = Category.objects.all()

    context = {
        'equipment_list': equipment_qs,
        'categories': categories,
        'filter_form': filter_form,
        'total_count': equipment_qs.count(),
    }
    return render(request, 'equipment/equipment_list.html', context)


@login_required
def equipment_detail_view(request, pk):
    """
    Equipment Details (Read operation):
    - Detailed hardware specifications, storage location, and availability.
    """
    item = get_object_or_404(Equipment.objects.select_related('category'), pk=pk)
    context = {
        'item': item,
    }
    return render(request, 'equipment/equipment_detail.html', context)


@custodian_required
def equipment_create_view(request):
    """
    Equipment Creation (Create operation):
    - Custodian / Staff only.
    - Registers new hardware into the laboratory database.
    """
    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES)
        if form.is_valid():
            equipment = form.save()
            messages.success(
                request,
                f"Equipment '{equipment.name}' ({equipment.asset_code}) registered successfully into inventory."
            )
            return redirect('equipment_detail', pk=equipment.pk)
        else:
            messages.error(request, "Failed to register equipment. Please correct the errors below.")
    else:
        form = EquipmentForm()

    return render(request, 'equipment/equipment_form.html', {
        'form': form,
        'action_title': 'Register New Lab Equipment',
        'is_create': True
    })


@custodian_required
def equipment_update_view(request, pk):
    """
    Equipment Modification (Update operation):
    - Custodian / Staff only.
    - Updates quantities, specs, storage location, or condition.
    """
    item = get_object_or_404(Equipment, pk=pk)

    if request.method == 'POST':
        form = EquipmentForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            equipment = form.save()
            messages.success(
                request,
                f"Equipment '{equipment.name}' updated successfully."
            )
            return redirect('equipment_detail', pk=equipment.pk)
        else:
            messages.error(request, "Failed to update equipment. Please check form errors.")
    else:
        form = EquipmentForm(instance=item)

    return render(request, 'equipment/equipment_form.html', {
        'form': form,
        'item': item,
        'action_title': f'Edit Equipment: {item.name}',
        'is_create': False
    })


@custodian_required
def equipment_delete_view(request, pk):
    """
    Equipment Deletion (Delete operation):
    - Custodian / Staff only.
    - Deletes or decommissions equipment from the inventory.
    """
    item = get_object_or_404(Equipment, pk=pk)

    if request.method == 'POST':
        item_name = item.name
        asset_code = item.asset_code
        item.delete()
        messages.success(
            request,
            f"Equipment '{item_name}' ({asset_code}) has been removed from inventory."
        )
        return redirect('equipment_list')

    return render(request, 'equipment/equipment_confirm_delete.html', {'item': item})
