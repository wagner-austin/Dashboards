/**
 * ALPR Investigation Dashboard - Main Navigation
 * Handles page routing and content loading
 */

const Router = {
    currentPage: null,
    cache: {},

    /**
     * Initialize the router
     */
    init() {
        this.bindNavigation();
        this.loadInitialPage();
    },

    /**
     * Bind click handlers to navigation links
     */
    bindNavigation() {
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.dataset.page;
                this.navigate(page);
            });
        });

        // Handle browser back/forward
        window.addEventListener('popstate', (e) => {
            if (e.state?.page) {
                this.loadPage(e.state.page, false);
            }
        });
    },

    /**
     * Load the initial page from URL hash or default to overview
     */
    loadInitialPage() {
        const hash = window.location.hash.slice(1);
        const page = hash || 'overview';
        this.loadPage(page, false);
    },

    /**
     * Navigate to a page and update URL
     */
    navigate(page) {
        window.location.hash = page;
        this.loadPage(page, true);
    },

    /**
     * Load page content into the container
     */
    async loadPage(page, pushState = true) {
        const container = document.getElementById('page-content');

        // Update active nav state
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.toggle('active', link.dataset.page === page);
        });

        // Check cache first
        if (this.cache[page]) {
            container.innerHTML = this.cache[page];
            this.onPageLoad(page);
            return;
        }

        // Load page content
        try {
            const response = await fetch(`pages/${page}.html`);
            if (!response.ok) throw new Error('Page not found');

            const content = await response.text();
            this.cache[page] = content;
            container.innerHTML = content;
            this.onPageLoad(page);

        } catch (error) {
            container.innerHTML = `
                <div class="section">
                    <h2>Page Not Found</h2>
                    <p>The page "${page}" could not be loaded.</p>
                </div>
            `;
        }

        this.currentPage = page;
    },

    /**
     * Called after page content is loaded
     */
    onPageLoad(page) {
        // Re-initialize interactive components
        if (typeof Utils !== 'undefined') {
            Utils.initAll();
        }

        // Scroll to top
        window.scrollTo(0, 0);
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    Router.init();
});
