from django import forms
from .models import Item, LifeCategory


class ItemForm(forms.ModelForm):
    """Form for creating a new Item."""
    
    new_category = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Or type new category...',
            'class': 'win95-input'
        })
    )

    class Meta:
        model = Item
        fields = ['note', 'type', 'action_length', 'time_frame', 'value', 'difficulty', 'life_category']
        widgets = {
            'note': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'What do you want to capture?',
                'class': 'win95-input win95-textarea',
                'autofocus': True,
            }),
            'type': forms.Select(attrs={'class': 'win95-select'}),
            'action_length': forms.Select(attrs={'class': 'win95-select'}),
            'time_frame': forms.Select(attrs={'class': 'win95-select'}),
            'value': forms.Select(attrs={'class': 'win95-select'}),
            'difficulty': forms.Select(attrs={'class': 'win95-select'}),
            'life_category': forms.Select(attrs={'class': 'win95-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add empty option for life_category
        self.fields['life_category'].empty_label = '—'
        self.fields['life_category'].required = False

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Handle new category creation
        new_category_name = self.cleaned_data.get('new_category', '').strip()
        if new_category_name:
            # New category takes precedence over existing selection
            category, created = LifeCategory.objects.get_or_create(name=new_category_name)
            instance.life_category = category
        
        if commit:
            instance.save()
        return instance

