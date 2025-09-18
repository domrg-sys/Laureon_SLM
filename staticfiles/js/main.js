/**
 * Main application script for Laureon MRP.
 *
 * This script initializes all primary UI components after the DOM is fully loaded.
 * It uses a single, namespaced `App` object as an entry point to avoid
 * polluting the global scope.
 *
 * @namespace App
 */
const App = {
    /**
     * Initializes all application components. This is the single entry point.
     */
    init() {
        // --- General UI Components ---
        this.initTabSlider();
        this.initCollapsibleTree();
        this.initTreeCollapseExpandAll();
        this.initDynamicGridColumns();
        this.initClosableMessages();
        this.initFormTabs();
        this.initToggleableFormField();

        // --- Page-Specific Interactive Components ---
        this.initializeBulkAddMode();
        this.initializeBulkDeleteMode();
        this.initializeTableBulkDelete();
    },

    // ========================================================================
    // General UI Component Initializers
    // ========================================================================

    /**
     * Manages the animated slider for tab navigation.
     */
    initTabSlider() {
        const nav = document.querySelector('.tab-nav');
        if (!nav) return;

        const slider = nav.querySelector('.tab-nav-slider');
        const activeTab = nav.querySelector('.tab-nav-item.is-active');
        if (!slider || !activeTab) return;

        const moveSlider = () => {
            slider.style.width = `${activeTab.offsetWidth}px`;
            slider.style.left = `${activeTab.offsetLeft}px`;
        };

        moveSlider(); // Set initial position on load
        window.addEventListener('resize', moveSlider); // Adjust on window resize
    },

    /**
     * Manages the collapsible tree view using event delegation for efficiency.
     */
    initCollapsibleTree() {
        const tree = document.querySelector('.location-tree');
        if (!tree) return;

        tree.addEventListener('click', (e) => {
            const toggleBtn = e.target.closest('.tree-toggle-btn');
            if (!toggleBtn) return;

            const targetId = toggleBtn.dataset.target;
            const childrenList = document.querySelector(targetId);
            if (!childrenList) return;

            const icon = toggleBtn.querySelector('.material-symbols-outlined');
            const isCollapsed = childrenList.classList.toggle('collapsed');

            icon.textContent = isCollapsed ? 'chevron_right' : 'expand_more';
        });
    },

    /**
     * Adds event listeners for the "Expand All" and "Collapse All" tree buttons.
     */
    initTreeCollapseExpandAll() {
        const tree = document.querySelector('.location-tree');
        if (!tree) return;

        const expandBtn = document.getElementById('expand-all-btn');
        const collapseBtn = document.getElementById('collapse-all-btn');

        if (expandBtn) {
            expandBtn.addEventListener('click', () => this.toggleAllTreeNodes(tree, false));
        }
        if (collapseBtn) {
            collapseBtn.addEventListener('click', () => this.toggleAllTreeNodes(tree, true));
        }
    },

    /**
     * Helper function to expand or collapse all nodes in a tree.
     * @param {HTMLElement} tree - The root ul element of the tree.
     * @param {boolean} collapse - Whether to collapse (true) or expand (false).
     */
    toggleAllTreeNodes(tree, collapse) {
        const toggles = tree.querySelectorAll('.tree-toggle-btn');
        const childrenLists = tree.querySelectorAll('.location-tree-children');
        const icon = collapse ? 'chevron_right' : 'expand_more';

        childrenLists.forEach(list => list.classList.toggle('collapsed', collapse));
        toggles.forEach(toggle => {
            toggle.querySelector('.material-symbols-outlined').textContent = icon;
        });
    },

    /**
     * Sets grid-template-columns for any element with a `data-cols` attribute.
     */
    initDynamicGridColumns() {
        document.querySelectorAll('[data-cols]').forEach(grid => {
            const cols = grid.dataset.cols;
            if (cols) {
                grid.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
            }
        });
    },

    /**
     * Manages form sections where a checkbox toggles the state of child fields.
     */
    initToggleableFormField() {
        document.querySelectorAll('[data-toggles-fields]').forEach(section => {
            const checkbox = section.querySelector('input[type="checkbox"]');
            const childFields = section.querySelectorAll('.form-field-group input, .form-field-group select');
            if (!checkbox || childFields.length === 0 || checkbox.disabled) {
                return;
            }

            const toggleFields = () => {
                childFields.forEach(input => {
                    input.disabled = !checkbox.checked;
                    if (!checkbox.checked) {
                        input.value = ''; // Clear value when disabling
                    }
                });
            };

            toggleFields(); // Set initial state
            checkbox.addEventListener('change', toggleFields);
        });
    },

    /**
     * Adds dismiss functionality to message banners.
     */
    initClosableMessages() {
        const container = document.querySelector('.messages-container');
        if (!container) return;

        container.addEventListener('click', (e) => {
            if (e.target.classList.contains('message-close')) {
                const message = e.target.parentElement;
                message.style.opacity = '0';
                // Remove the element after the fade-out transition completes.
                setTimeout(() => message.remove(), 300);
            }
        });
    },

    /**
     * Initializes the tabbed interface used on some forms.
     */
    initFormTabs() {
        const tabContainer = document.querySelector('.tab-nav-form');
        if (!tabContainer) return;

        const tabLinks = tabContainer.querySelectorAll('.tab-link-form');
        const tabContents = document.querySelectorAll('.tab-content-form');

        tabLinks.forEach(link => {
            link.addEventListener('click', () => {
                const tabId = link.dataset.tab;
                tabLinks.forEach(item => item.classList.remove('is-active'));
                link.classList.add('is-active');

                tabContents.forEach(content => {
                    content.classList.toggle('is-active', content.id === tabId);
                });
            });
        });
    },

    // ========================================================================
    // Page-Specific Interactive Components
    // ========================================================================

    /**
     * Handles the UI for selecting multiple grid cells for bulk sample creation.
     */
    initializeBulkAddMode() {
        const toggleBtn = document.getElementById('bulk-add-toggle-btn');
        const cancelBtn = document.getElementById('bulk-add-cancel-btn');
        const proceedBtn = document.getElementById('bulk-add-proceed-btn');
        const countSpan = document.getElementById('bulk-add-count');
        const grid = document.querySelector('.space-grid');
        const hiddenInputsContainer = document.getElementById('bulk-add-hidden-inputs');
        const bulkDeleteToggleBtn = document.getElementById('bulk-delete-toggle-btn');

        if (!toggleBtn || !grid) return;

        let isSelectionMode = false;
        const selectedCells = new Set();
        let lastSelectedCoord = null;

        const updateUI = () => {
            grid.classList.toggle('selection-mode', isSelectionMode);
            toggleBtn.style.display = isSelectionMode ? 'none' : 'inline-flex';
            cancelBtn.style.display = isSelectionMode ? 'inline-flex' : 'none';
            proceedBtn.style.display = isSelectionMode ? 'inline-flex' : 'none';
            if (bulkDeleteToggleBtn) {
                bulkDeleteToggleBtn.disabled = isSelectionMode;
            }

            if (!isSelectionMode) {
                document.querySelectorAll('.space-cell.is-selected').forEach(cell => {
                    cell.classList.remove('is-selected');
                });
                selectedCells.clear();
                lastSelectedCoord = null;
            }

            const count = selectedCells.size;
            countSpan.textContent = count;
            proceedBtn.disabled = count === 0;

            hiddenInputsContainer.innerHTML = '';
            selectedCells.forEach(coord => {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'selected_spaces';
                input.value = coord;
                hiddenInputsContainer.appendChild(input);
            });
        };

        toggleBtn.addEventListener('click', () => { isSelectionMode = true; updateUI(); });
        cancelBtn.addEventListener('click', () => { isSelectionMode = false; updateUI(); });

        grid.addEventListener('click', (e) => {
            if (!isSelectionMode) return;

            e.preventDefault();

            const cell = e.target.closest('.space-available');
            if (!cell) return;

            const currentCoord = cell.dataset.coord;

            if (e.shiftKey && lastSelectedCoord) {
                const [startRow, startCol] = lastSelectedCoord.split(',').map(Number);
                const [endRow, endCol] = currentCoord.split(',').map(Number);
                const minRow = Math.min(startRow, endRow);
                const maxRow = Math.max(startRow, endRow);
                const minCol = Math.min(startCol, endCol);
                const maxCol = Math.max(startCol, endCol);

                grid.querySelectorAll('.space-available').forEach(cellInRange => {
                    const [row, col] = cellInRange.dataset.coord.split(',').map(Number);
                    if (row >= minRow && row <= maxRow && col >= minCol && col <= maxCol) {
                        selectedCells.add(cellInRange.dataset.coord);
                        cellInRange.classList.add('is-selected');
                    }
                });
            } else {
                if (selectedCells.has(currentCoord)) {
                    selectedCells.delete(currentCoord);
                    cell.classList.remove('is-selected');
                } else {
                    selectedCells.add(currentCoord);
                    cell.classList.add('is-selected');
                }
                lastSelectedCoord = currentCoord;
            }
            updateUI();
        });
    },

    /**
     * Handles the UI for selecting multiple grid cells for bulk sample deletion.
     */
    initializeBulkDeleteMode() {
        const form = document.getElementById('bulk-delete-form');
        const toggleBtn = document.getElementById('bulk-delete-toggle-btn');
        const cancelBtn = document.getElementById('bulk-delete-cancel-btn');
        const proceedBtn = document.getElementById('bulk-delete-proceed-btn');
        const countSpan = document.getElementById('bulk-delete-count');
        const grid = document.querySelector('.space-grid');
        const hiddenInputsContainer = document.getElementById('bulk-delete-hidden-inputs');
        const bulkAddToggleBtn = document.getElementById('bulk-add-toggle-btn');

        if (!toggleBtn || !grid || !form) return;

        let isSelectionMode = false;
        const selectedSamples = new Map(); // Use a map to store pk -> coord
        let lastSelectedCoord = null;

        const updateUI = () => {
            grid.classList.toggle('selection-mode-delete', isSelectionMode);
            toggleBtn.style.display = isSelectionMode ? 'none' : 'inline-flex';
            cancelBtn.style.display = isSelectionMode ? 'inline-flex' : 'none';
            proceedBtn.style.display = isSelectionMode ? 'inline-flex' : 'none';
            if (bulkAddToggleBtn) {
                bulkAddToggleBtn.disabled = isSelectionMode;
            }

            if (!isSelectionMode) {
                document.querySelectorAll('.space-cell.is-selected-delete').forEach(cell => {
                    cell.classList.remove('is-selected-delete');
                });
                selectedSamples.clear();
                lastSelectedCoord = null;
            }

            const count = selectedSamples.size;
            countSpan.textContent = count;
            proceedBtn.disabled = count === 0;

            hiddenInputsContainer.innerHTML = '';
            selectedSamples.forEach((coord, pk) => {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = 'selected_samples';
                input.value = pk;
                hiddenInputsContainer.appendChild(input);
            });
        };

        toggleBtn.addEventListener('click', () => { isSelectionMode = true; updateUI(); });
        cancelBtn.addEventListener('click', () => { isSelectionMode = false; updateUI(); });

        grid.addEventListener('click', (e) => {
            if (!isSelectionMode) return;

            e.preventDefault();

            const cell = e.target.closest('.space-interactable[data-sample-pk]');
            if (!cell) return;

            const samplePk = cell.dataset.samplePk;
            const currentCoord = cell.dataset.coord;

            if (e.shiftKey && lastSelectedCoord) {
                const [startRow, startCol] = lastSelectedCoord.split(',').map(Number);
                const [endRow, endCol] = currentCoord.split(',').map(Number);
                const minRow = Math.min(startRow, endRow);
                const maxRow = Math.max(startRow, endRow);
                const minCol = Math.min(startCol, endCol);
                const maxCol = Math.max(startCol, endCol);

                grid.querySelectorAll('.space-interactable[data-sample-pk]').forEach(cellInRange => {
                    const [row, col] = cellInRange.dataset.coord.split(',').map(Number);
                    if (row >= minRow && row <= maxRow && col >= minCol && col <= maxCol) {
                        selectedSamples.set(cellInRange.dataset.samplePk, cellInRange.dataset.coord);
                        cellInRange.classList.add('is-selected-delete');
                    }
                });
            } else {
                if (selectedSamples.has(samplePk)) {
                    selectedSamples.delete(samplePk);
                    cell.classList.remove('is-selected-delete');
                } else {
                    selectedSamples.set(samplePk, currentCoord);
                    cell.classList.add('is-selected-delete');
                }
                lastSelectedCoord = currentCoord;
            }
            updateUI();
        });
    },

    /**
     * Handles checkbox selection for bulk deletion in a table view.
     */
    initializeTableBulkDelete() {
        const form = document.getElementById('bulk-delete-table-form');
        if (!form) return;

        const selectAllCheckbox = document.getElementById('select-all-checkbox');
        const sampleCheckboxes = form.querySelectorAll('.sample-checkbox');
        const deleteBtn = document.getElementById('bulk-delete-table-btn');

        if (!selectAllCheckbox || sampleCheckboxes.length === 0 || !deleteBtn) return;

        const updateButtonState = () => {
            const anyChecked = Array.from(sampleCheckboxes).some(cb => cb.checked);
            deleteBtn.disabled = !anyChecked;
        };

        selectAllCheckbox.addEventListener('change', () => {
            sampleCheckboxes.forEach(checkbox => {
                checkbox.checked = selectAllCheckbox.checked;
            });
            updateButtonState();
        });

        sampleCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                if (!checkbox.checked) {
                    selectAllCheckbox.checked = false;
                }
                updateButtonState();
            });
        });

        updateButtonState();
    }
};

// --- Main Entry Point ---
// Ensures all scripts run only after the entire page is loaded.
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});