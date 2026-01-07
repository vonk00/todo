/**
 * Nowpad Organize Page - Inline Editing JavaScript
 * Handles instant-save behavior for inline edits
 */

(function() {
    'use strict';

    // Configuration
    const DEBOUNCE_DELAY = 500; // ms delay for text input saves
    const CSRF_TOKEN = document.querySelector('[name=csrfmiddlewaretoken]')?.value || getCookie('csrftoken');

    // Track pending saves for debouncing
    const pendingSaves = new Map();

    // Create and append saving indicator
    const savingIndicator = document.createElement('div');
    savingIndicator.className = 'saving-indicator';
    savingIndicator.textContent = 'Saving...';
    document.body.appendChild(savingIndicator);

    /**
     * Get CSRF token from cookies
     */
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /**
     * Show the saving indicator
     */
    function showSaving() {
        savingIndicator.textContent = 'Saving...';
        savingIndicator.className = 'saving-indicator visible';
    }

    /**
     * Show save success
     */
    function showSaveSuccess() {
        savingIndicator.textContent = '✓ Saved';
        savingIndicator.className = 'saving-indicator visible save-success';
        setTimeout(() => {
            savingIndicator.className = 'saving-indicator';
        }, 1500);
    }

    /**
     * Show save error
     */
    function showSaveError(message) {
        savingIndicator.textContent = '✗ ' + (message || 'Error');
        savingIndicator.className = 'saving-indicator visible save-error';
        setTimeout(() => {
            savingIndicator.className = 'saving-indicator';
        }, 3000);
    }

    /**
     * Get the item ID from a DOM element
     */
    function getItemId(element) {
        const row = element.closest('[data-item-id]');
        return row ? row.dataset.itemId : null;
    }

    /**
     * Save a field value to the server
     */
    async function saveField(itemId, field, value, element) {
        showSaving();

        try {
            const response = await fetch(`/x9K3pQ7v2/api/item/${itemId}/update/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN,
                },
                body: JSON.stringify({ field, value }),
            });

            const data = await response.json();

            if (data.success) {
                showSaveSuccess();
                element.classList.add('field-updated');
                setTimeout(() => element.classList.remove('field-updated'), 500);

                // Update UI based on response
                updateUIAfterSave(itemId, data.item, element);
            } else {
                showSaveError(data.error);
                element.classList.add('field-error');
                setTimeout(() => element.classList.remove('field-error'), 1000);
            }
        } catch (error) {
            console.error('Save error:', error);
            showSaveError('Network error');
            element.classList.add('field-error');
            setTimeout(() => element.classList.remove('field-error'), 1000);
        }
    }

    /**
     * Update UI after a successful save
     */
    function updateUIAfterSave(itemId, item, triggerElement) {
        const row = document.querySelector(`[data-item-id="${itemId}"]`);
        if (!row) return;

        // Update score display
        const scoreElements = row.querySelectorAll('.score-value');
        scoreElements.forEach(el => {
            el.textContent = item.score !== null ? item.score : '—';
        });

        // Handle type change - enable/disable action_length
        const typeSelect = triggerElement.dataset.field === 'type' ? triggerElement : null;
        if (typeSelect) {
            const isAction = item.type === 'Action';
            
            // Desktop view
            const actionLengthCell = row.querySelector('.cell-action-length');
            if (actionLengthCell) {
                const actionSelect = actionLengthCell.querySelector('select');
                actionLengthCell.style.opacity = isAction ? '1' : '0.3';
                if (actionSelect) {
                    actionSelect.disabled = !isAction;
                    if (!isAction) actionSelect.value = '';
                }
            }
            
            // Mobile view
            const mobileActionField = row.querySelector('.card-action-length');
            if (mobileActionField) {
                mobileActionField.style.display = isAction ? 'block' : 'none';
                const mobileSelect = mobileActionField.querySelector('select');
                if (mobileSelect && !isAction) mobileSelect.value = '';
            }
        }

        // Clear action_length in UI if it was cleared server-side
        if (item.action_length === '' && triggerElement.dataset.field !== 'action_length') {
            const actionLengthSelects = row.querySelectorAll('[data-field="action_length"]');
            actionLengthSelects.forEach(select => {
                select.value = '';
            });
        }

        // Update card preview if note was changed
        if (triggerElement.dataset.field === 'note') {
            const preview = row.querySelector('.card-note-preview');
            if (preview) {
                const noteText = item.note;
                preview.textContent = noteText.length > 60 ? noteText.substring(0, 60) + '...' : noteText;
            }
        }
    }

    /**
     * Handle select change (instant save)
     */
    function handleSelectChange(event) {
        const select = event.target;
        const itemId = getItemId(select);
        const field = select.dataset.field;
        const value = select.value;

        if (itemId && field) {
            saveField(itemId, field, value, select);
        }
    }

    /**
     * Handle text input with debounce (save on blur or after typing stops)
     */
    function handleTextInput(event) {
        const input = event.target;
        const itemId = getItemId(input);
        const field = input.dataset.field;

        if (!itemId || !field) return;

        // Clear existing pending save
        const key = `${itemId}-${field}`;
        if (pendingSaves.has(key)) {
            clearTimeout(pendingSaves.get(key));
        }

        // Set new pending save with debounce
        const timeoutId = setTimeout(() => {
            saveField(itemId, field, input.value, input);
            pendingSaves.delete(key);
        }, DEBOUNCE_DELAY);

        pendingSaves.set(key, timeoutId);
    }

    /**
     * Handle text blur (save immediately)
     */
    function handleTextBlur(event) {
        const input = event.target;
        const itemId = getItemId(input);
        const field = input.dataset.field;

        if (!itemId || !field) return;

        // Cancel pending debounced save and save immediately
        const key = `${itemId}-${field}`;
        if (pendingSaves.has(key)) {
            clearTimeout(pendingSaves.get(key));
            pendingSaves.delete(key);
        }

        saveField(itemId, field, input.value, input);
    }

    /**
     * Initialize event listeners for inline editing
     */
    function initInlineEditing() {
        // Select elements - save on change
        document.querySelectorAll('.inline-edit').forEach(element => {
            if (element.tagName === 'SELECT') {
                element.addEventListener('change', handleSelectChange);
            } else if (element.tagName === 'TEXTAREA' || element.tagName === 'INPUT') {
                element.addEventListener('input', handleTextInput);
                element.addEventListener('blur', handleTextBlur);
            }
        });
    }

    /**
     * Initialize sorting
     */
    function initSorting() {
        document.querySelectorAll('.sortable').forEach(th => {
            th.addEventListener('click', function() {
                const field = this.dataset.sort;
                const currentSort = new URLSearchParams(window.location.search).get('sort') || '-date_created';
                
                // Toggle sort direction
                let newSort;
                if (currentSort === field) {
                    newSort = '-' + field;
                } else if (currentSort === '-' + field) {
                    newSort = field;
                } else {
                    newSort = field;
                }

                // Update URL and reload
                const params = new URLSearchParams(window.location.search);
                params.set('sort', newSort);
                window.location.search = params.toString();
            });
        });
    }

    // Initialize on DOM ready
    document.addEventListener('DOMContentLoaded', function() {
        initInlineEditing();
        initSorting();
    });

    // Expose toggleCard for mobile view
    window.toggleCard = function(header) {
        const card = header.closest('.item-card');
        if (card) {
            card.classList.toggle('expanded');
        }
    };

})();

