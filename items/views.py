import json
import random
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
    from django.db.models import Q
    
    # Get filter parameters (all multi-select)
    status_filters = request.GET.getlist('status')
    if not status_filters:
        status_filters = ['Open']  # Default to Open
    
    time_frame_filters = request.GET.getlist('time_frame')
    if not time_frame_filters:
        time_frame_filters = ['Today']  # Default to Today
    
    type_filters = request.GET.getlist('type')
    category_filters = request.GET.getlist('category')
    value_filters = request.GET.getlist('value')
    difficulty_filters = request.GET.getlist('difficulty')
    
    # Get sort parameter (default: newest first)
    sort_by = request.GET.get('sort', '-date_created')
    
    # Build queryset
    items = Item.objects.all()
    
    # Apply status filter
    if status_filters:
        status_q = Q()
        regular_statuses = [s for s in status_filters if s != '__empty__']
        if regular_statuses:
            status_q |= Q(status__in=regular_statuses)
        if '__empty__' in status_filters:
            status_q |= Q(status='')
        items = items.filter(status_q)
    
    # Apply time frame filter
    if time_frame_filters:
        tf_q = Q()
        regular_tfs = [tf for tf in time_frame_filters if tf != '__empty__']
        if regular_tfs:
            tf_q |= Q(time_frame__in=regular_tfs)
        if '__empty__' in time_frame_filters:
            tf_q |= Q(time_frame='')
        items = items.filter(tf_q)
    
    # Apply type filter
    if type_filters:
        type_q = Q()
        regular_types = [t for t in type_filters if t != '__empty__']
        if regular_types:
            type_q |= Q(type__in=regular_types)
        if '__empty__' in type_filters:
            type_q |= Q(type='')
        items = items.filter(type_q)
    
    # Apply category filter
    if category_filters:
        cat_q = Q()
        regular_cats = [c for c in category_filters if c != '__empty__']
        if regular_cats:
            cat_q |= Q(life_category_id__in=regular_cats)
        if '__empty__' in category_filters:
            cat_q |= Q(life_category__isnull=True)
        items = items.filter(cat_q)
    
    # Apply value filter
    if value_filters:
        val_q = Q()
        regular_vals = [v for v in value_filters if v != '__empty__']
        if regular_vals:
            val_q |= Q(value__in=[int(v) for v in regular_vals])
        if '__empty__' in value_filters:
            val_q |= Q(value__isnull=True)
        items = items.filter(val_q)
    
    # Apply difficulty filter
    if difficulty_filters:
        diff_q = Q()
        regular_diffs = [d for d in difficulty_filters if d != '__empty__']
        if regular_diffs:
            diff_q |= Q(difficulty__in=[int(d) for d in regular_diffs])
        if '__empty__' in difficulty_filters:
            diff_q |= Q(difficulty__isnull=True)
        items = items.filter(diff_q)
    
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
        'current_statuses': status_filters,
        'current_time_frames': time_frame_filters,
        'current_types': type_filters,
        'current_categories': category_filters,
        'current_values': value_filters,
        'current_difficulties': difficulty_filters,
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


def roulette(request):
    """View for the Roulette page - randomly select an open item."""
    # Get filter parameters (all multi-select)
    type_filters = request.GET.getlist('type')
    time_frame_filters = request.GET.getlist('time_frame')
    action_length_filters = request.GET.getlist('action_length')
    value_min = request.GET.get('value_min', '')
    value_max = request.GET.get('value_max', '')
    difficulty_min = request.GET.get('difficulty_min', '')
    difficulty_max = request.GET.get('difficulty_max', '')
    do_roll = request.GET.get('roll', '')
    
    # Build queryset - always filter by Open status
    items = Item.objects.filter(status='Open')
    
    # Apply filters
    if type_filters:
        items = items.filter(type__in=type_filters)
    
    if time_frame_filters:
        items = items.filter(time_frame__in=time_frame_filters)
    
    if action_length_filters:
        items = items.filter(action_length__in=action_length_filters)
    
    if value_min:
        try:
            items = items.filter(value__gte=int(value_min))
        except ValueError:
            pass
    
    if value_max:
        try:
            items = items.filter(value__lte=int(value_max))
        except ValueError:
            pass
    
    if difficulty_min:
        try:
            items = items.filter(difficulty__gte=int(difficulty_min))
        except ValueError:
            pass
    
    if difficulty_max:
        try:
            items = items.filter(difficulty__lte=int(difficulty_max))
        except ValueError:
            pass
    
    # Get matching count
    matching_count = items.count()
    
    # Roll for a random item if requested
    selected_item = None
    if do_roll and matching_count > 0:
        random_index = random.randint(0, matching_count - 1)
        selected_item = items[random_index]
    
    context = {
        'selected_item': selected_item,
        'matching_count': matching_count,
        'current_types': type_filters,
        'current_time_frames': time_frame_filters,
        'current_action_lengths': action_length_filters,
        'current_value_min': value_min,
        'current_value_max': value_max,
        'current_difficulty_min': difficulty_min,
        'current_difficulty_max': difficulty_max,
        'type_choices': Item.TYPE_CHOICES,
        'time_frame_choices': Item.TIME_FRAME_CHOICES,
        'action_length_choices': Item.ACTION_LENGTH_CHOICES,
        'rating_choices': Item.RATING_CHOICES,
        'did_roll': bool(do_roll),
    }
    
    return render(request, 'items/roulette.html', context)

