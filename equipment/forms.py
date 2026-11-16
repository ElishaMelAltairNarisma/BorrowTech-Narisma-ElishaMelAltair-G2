from django import forms
from .models import Equipment, Category


class EquipmentForm(forms.ModelForm):
    class Meta:
        model = Equipment
        fields = [
            'name',
            'asset_code',
            'category',
            'model_number',
            'description',
            'total_quantity',
            'available_quantity',
            'laboratory_room',
            'storage_location',
            'condition',
            'image',
            'is_active',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'e.g., Arduino Uno R3 Starter Kit',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none transition'
            }),
            'asset_code': forms.TextInput(attrs={
                'placeholder': 'e.g., EQ-ARD-010',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none transition'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none transition'
            }),
            'model_number': forms.TextInput(attrs={
                'placeholder': 'e.g., A000066',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none transition'
            }),
            'description': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Include technical specifications, accessories included (cables, sensors, adapters), and lab usage guidelines...',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none transition'
            }),
            'total_quantity': forms.NumberInput(attrs={
                'min': 1,
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none transition'
            }),
            'available_quantity': forms.NumberInput(attrs={
                'min': 0,
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none transition'
            }),
            'laboratory_room': forms.TextInput(attrs={
                'placeholder': 'e.g., Room 402 - IT Hardware Laboratory',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none transition'
            }),
            'storage_location': forms.TextInput(attrs={
                'placeholder': 'e.g., Cabinet A - Shelf 2',
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none transition'
            }),
            'condition': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:outline-none transition'
            }),
            'image': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-slate-500 file:mr-4 file:py-2.5 file:px-4 file:rounded-lg file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 transition'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get('total_quantity')
        available = cleaned_data.get('available_quantity')
        if total is not None and available is not None and available > total:
            self.add_error('available_quantity', 'Available quantity cannot exceed total inventory quantity.')
        return cleaned_data


class EquipmentFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search by equipment name, asset code, or model...',
            'class': 'w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-300 bg-white text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={
            'class': 'px-3 py-2.5 rounded-xl border border-slate-300 bg-white text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none'
        })
    )
    availability = forms.ChoiceField(
        choices=[
            ('all', 'All Statuses'),
            ('available', 'Available Only'),
            ('limited', 'Limited Stock'),
            ('checked_out', 'Checked Out'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'px-3 py-2.5 rounded-xl border border-slate-300 bg-white text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none'
        })
    )
