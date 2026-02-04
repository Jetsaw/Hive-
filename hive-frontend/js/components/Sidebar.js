/**
 * Sidebar Component
 * Manages sidebar navigation and mobile menu
 */

/**
 * Initialize sidebar functionality
 */
export function initSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const navLinks = document.querySelectorAll('.nav-link');

    // Mobile menu toggle
    if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('active');
        });
    }

    // Close sidebar on mobile when clicking outside
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 1024) {
            if (!sidebar.contains(e.target) && !mobileMenuBtn.contains(e.target)) {
                sidebar.classList.remove('active');
            }
        }
    });

    // Navigation link active state
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const page = link.getAttribute('data-page');

            // Don't prevent default for external links (admin)
            if (!link.getAttribute('target')) {
                e.preventDefault();

                // Update active state
                navLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');

                // Close mobile menu
                if (window.innerWidth <= 1024) {
                    sidebar.classList.remove('active');
                }

                // Handle page navigation (placeholder for future SPA routing)
                handlePageNavigation(page);
            }
        });
    });

    // Programme selector
    const programmeSelect = document.getElementById('programmeSelect');
    if (programmeSelect) {
        programmeSelect.addEventListener('change', (e) => {
            const programme = e.target.value;
            console.log('Programme selected:', programme);
            // Here you could update the session with the programme
        });
    }
}

/**
 * Handle page navigation
 * @param {string} page - Page name
 */
function handlePageNavigation(page) {
    console.log('Navigate to:', page);

    // Placeholder for future routing logic
    // You can implement different views here
    switch (page) {
        case 'chat':
            // Show chat view (default)
            break;
        case 'history':
            // Show history view
            alert('History view - Coming soon!');
            break;
        case 'settings':
            // Show settings view
            alert('Settings view - Coming soon!');
            break;
    }
}
