/**
 * ALPR Investigation Dashboard - Utility Functions
 */

const Utils = {
    /**
     * Initialize all interactive components
     */
    initAll() {
        this.initCopyButtons();
        this.initCollapsibles();
    },

    /**
     * Initialize collapsible sections
     */
    initCollapsibles() {
        document.querySelectorAll('.collapsible-header').forEach(header => {
            header.addEventListener('click', () => {
                const collapsible = header.closest('.collapsible');
                collapsible.classList.toggle('open');
            });
        });
    },

    /**
     * Initialize copy-to-clipboard buttons
     */
    initCopyButtons() {
        document.querySelectorAll('.copy-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const targetId = btn.dataset.target;
                const target = document.getElementById(targetId);
                if (target) {
                    this.copyToClipboard(target.innerText, btn);
                }
            });
        });
    },

    /**
     * Copy text to clipboard and show feedback
     */
    async copyToClipboard(text, button) {
        try {
            await navigator.clipboard.writeText(text);
            const originalText = button.textContent;
            button.textContent = 'Copied!';
            setTimeout(() => {
                button.textContent = originalText;
            }, 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
            button.textContent = 'Failed';
        }
    },

    /**
     * Format a date string
     */
    formatDate(dateStr) {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }
};
