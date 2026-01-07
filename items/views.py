import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Item, LifeCategory
from .forms import ItemForm


def add_item(request):
    """View for the Add/Capture page."""
    if request.method == 'POST':
        form = ItemForm(request.POST)
        if form.is_valid():
            form.save()
            # Clear form after successful save
            return redirect('add_item')
    else:
        form = ItemForm()
    
    return render(request, 'items/add.html', {'form': form})


def organize(request):
    """View for the Organize page with filtering and sorting."""
    # Get filter parameters
    status_filter = request.GET.get('status', 'Open')
    time_frame_filter = request.GET.get('time_frame', 'Today')  # Default to Today
    type_filter = request.GET.get('type', '')
    category_filter = request.GET.get('category', '')
    value_filter = request.GET.get('value', '')
    difficulty_filter = request.GET.get('difficulty', '')
    
    # Get sort parameter (default: newest first)
    sort_by = request.GET.get('sort', '-date_created')
    
    # Build queryset
    items = Item.objects.all()
    
    # Apply filters (handle "Empty" option to find blank/null fields)
    if status_filter:
        if status_filter == '__empty__':
            items = items.filter(status='')
        else:
            items = items.filter(status=status_filter)
    
    if time_frame_filter:
        if time_frame_filter == '__empty__':
            items = items.filter(time_frame='')
        elif time_frame_filter != '__all__':  # Allow showing all if explicitly selected
            items = items.filter(time_frame=time_frame_filter)
    
    if type_filter:
        if type_filter == '__empty__':
            items = items.filter(type='')
        else:
            items = items.filter(type=type_filter)
    
    if category_filter:
        if category_filter == '__empty__':
            items = items.filter(life_category__isnull=True)
        else:
            items = items.filter(life_category_id=category_filter)
    
    if value_filter:
        if value_filter == '__empty__':
            items = items.filter(value__isnull=True)
        else:
            items = items.filter(value=value_filter)
    
    if difficulty_filter:
        if difficulty_filter == '__empty__':
            items = items.filter(difficulty__isnull=True)
        else:
            items = items.filter(difficulty=difficulty_filter)
    
    # Apply sorting
    valid_sort_fields = [
        'date_created', '-date_created',
        'note', '-note',
        'type', '-type',
        'time_frame', '-time_frame',
        'value', '-value',
        'difficulty', '-difficulty',
        'status', '-status',
        'date_completed', '-date_completed',
    ]
    if sort_by in valid_sort_fields:
        items = items.order_by(sort_by)
    else:
        items = items.order_by('-date_created')
    
    # Get all categories for filter dropdown
    categories = LifeCategory.objects.all()
    
    context = {
        'items': items,
        'categories': categories,
        'current_status': status_filter,
        'current_time_frame': time_frame_filter,
        'current_type': type_filter,
        'current_category': category_filter,
        'current_value': value_filter,
        'current_difficulty': difficulty_filter,
        'current_sort': sort_by,
        'status_choices': Item.STATUS_CHOICES,
        'time_frame_choices': Item.TIME_FRAME_CHOICES,
        'type_choices': Item.TYPE_CHOICES,
        'action_length_choices': Item.ACTION_LENGTH_CHOICES,
        'rating_choices': Item.RATING_CHOICES,
    }
    
    return render(request, 'items/organize.html', context)


@require_http_methods(["POST"])
def update_item(request, item_id):
    """
    Endpoint for inline edits.
    Accepts JSON: { "field": "field_name", "value": "new_value" }
    Returns JSON with updated item data.
    """
    item = get_object_or_404(Item, id=item_id)
    
    try:
        data = json.loads(request.body)
        field = data.get('field')
        value = data.get('value')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    # Allowed editable fields
    allowed_fields = ['note', 'type', 'action_length', 'time_frame', 'value', 'difficulty', 'status', 'life_category']
    
    if field not in allowed_fields:
        return JsonResponse({'success': False, 'error': f'Field not allowed: {field}'}, status=400)
    
    # Handle special cases
    if field == 'life_category':
        if value == '' or value is None:
            item.life_category = None
        elif str(value).startswith('new:'):
            # Create new category
            new_name = str(value)[4:].strip()
            if new_name:
                category, created = LifeCategory.objects.get_or_create(name=new_name)
                item.life_category = category
        else:
            try:
                category = LifeCategory.objects.get(id=int(value))
                item.life_category = category
            except (LifeCategory.DoesNotExist, ValueError):
                return JsonResponse({'success': False, 'error': 'Invalid category'}, status=400)
    elif field in ['value', 'difficulty']:
        # Handle integer fields
        if value == '' or value is None:
            setattr(item, field, None)
        else:
            try:
                int_value = int(value)
                if 1 <= int_value <= 5:
                    setattr(item, field, int_value)
                else:
                    return JsonResponse({'success': False, 'error': f'{field} must be between 1 and 5'}, status=400)
            except ValueError:
                return JsonResponse({'success': False, 'error': f'Invalid {field} value'}, status=400)
    else:
        # String fields
        setattr(item, field, value if value else '')
    
    # Save applies business rules (clear action_length if not Action, handle date_completed)
    item.save()
    
    # Return updated item data
    response_data = {
        'success': True,
        'item': {
            'id': item.id,
            'note': item.note,
            'type': item.type,
            'action_length': item.action_length,
            'time_frame': item.time_frame,
            'value': item.value,
            'difficulty': item.difficulty,
            'status': item.status,
            'life_category_id': item.life_category_id,
            'life_category_name': item.life_category.name if item.life_category else '',
            'score': item.score,
            'date_completed': item.date_completed.isoformat() if item.date_completed else None,
        }
    }
    
    return JsonResponse(response_data)


def get_categories(request):
    """Return all categories as JSON for dynamic dropdowns."""
    categories = list(LifeCategory.objects.values('id', 'name'))
    return JsonResponse({'categories': categories})

