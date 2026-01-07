from django.db import models
from django.utils import timezone


class LifeCategory(models.Model):
    """User-defined category for organizing items."""
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Life Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Item(models.Model):
    """Main table representing a captured note/task/idea."""
    
    # Type choices
    TYPE_CHOICES = [
        ('', '—'),
        ('Idea', 'Idea'),
        ('Journey', 'Journey'),
        ('Project', 'Project'),
        ('Action', 'Action'),
    ]
    
    # Action length choices (only meaningful when type == Action)
    ACTION_LENGTH_CHOICES = [
        ('', '—'),
        ('5 minutes', '5 minutes'),
        ('15 minutes', '15 minutes'),
        ('1 hour', '1 hour'),
        ('3 hours', '3 hours'),
    ]
    
    # Time frame choices
    TIME_FRAME_CHOICES = [
        ('', '—'),
        ('Now', 'Now'),
        ('Today', 'Today'),
        ('This Week', 'This Week'),
        ('This Month', 'This Month'),
        ('Future', 'Future'),
    ]
    
    # Status choices
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Complete', 'Complete'),
        ('Archive', 'Archive'),
        ('Remove', 'Remove'),
    ]
    
    # Value and Difficulty range
    RATING_CHOICES = [
        (None, '—'),
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    ]

    # Fields
    note = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, blank=True, default='')
    action_length = models.CharField(max_length=20, choices=ACTION_LENGTH_CHOICES, blank=True, default='')
    time_frame = models.CharField(max_length=20, choices=TIME_FRAME_CHOICES, blank=True, default='')
    value = models.IntegerField(null=True, blank=True, choices=RATING_CHOICES)
    difficulty = models.IntegerField(null=True, blank=True, choices=RATING_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Open')
    life_category = models.ForeignKey(
        LifeCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='items'
    )
    date_created = models.DateTimeField(auto_now_add=True)
    date_completed = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-date_created']

    def __str__(self):
        return self.note[:50] + ('...' if len(self.note) > 50 else '')

    @property
    def score(self):
        """
        Computed score for prioritization.
        Formula: score = value + (6 - difficulty)
        Range: 2-10, where 10 is best (high value, low difficulty).
        Returns None if value or difficulty is not set.
        """
        if self.value is not None and self.difficulty is not None:
            return self.value + (6 - self.difficulty)
        return None

    def save(self, *args, **kwargs):
        """Apply business rules before saving."""
        # Rule: If type != Action, clear action_length
        if self.type != 'Action':
            self.action_length = ''
        
        # Rule: If status is Complete, set date_completed if not already set
        if self.status == 'Complete':
            if self.date_completed is None:
                self.date_completed = timezone.now()
        else:
            # Rule: If status is not Complete, clear date_completed
            self.date_completed = None
        
        super().save(*args, **kwargs)

