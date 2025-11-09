// Dashboard Sidebar Toggle Script
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.dashboard-sidebar');
    const content = document.querySelector('.dashboard-content');
    const toggleBtn = document.querySelector('.sidebar-toggle');

    if (!sidebar || !content || !toggleBtn) return;

    // Load saved state from localStorage
    const sidebarState = localStorage.getItem('sidebarCollapsed');
    if (sidebarState === 'true') {
        sidebar.classList.add('collapsed');
        content.classList.add('expanded');
        toggleBtn.classList.remove('shifted');
    } else {
        toggleBtn.classList.add('shifted');
    }

    // Toggle sidebar on button click
    toggleBtn.addEventListener('click', function() {
        const isCollapsed = sidebar.classList.toggle('collapsed');
        content.classList.toggle('expanded');
        toggleBtn.classList.toggle('shifted');

        // Save state to localStorage
        localStorage.setItem('sidebarCollapsed', isCollapsed);

        // Add animation class
        this.style.transform = 'rotate(180deg)';
        setTimeout(() => {
            this.style.transform = 'rotate(0deg)';
        }, 300);
    });

    // Highlight active menu item based on current URL
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar-nav-link');

    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // Mobile: close sidebar when clicking outside
    document.addEventListener('click', function(event) {
        if (window.innerWidth <= 768) {
            if (!sidebar.contains(event.target) &&
                !toggleBtn.contains(event.target) &&
                !sidebar.classList.contains('collapsed')) {
                sidebar.classList.add('collapsed');
                content.classList.add('expanded');
                toggleBtn.classList.remove('shifted');
                localStorage.setItem('sidebarCollapsed', 'true');
            }
        }
    });

    // Handle window resize
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            if (window.innerWidth > 768) {
                // Restore saved state on desktop
                const sidebarState = localStorage.getItem('sidebarCollapsed');
                if (sidebarState === 'true') {
                    sidebar.classList.add('collapsed');
                    content.classList.add('expanded');
                    toggleBtn.classList.remove('shifted');
                } else {
                    sidebar.classList.remove('collapsed');
                    content.classList.remove('expanded');
                    toggleBtn.classList.add('shifted');
                }
            }
        }, 250);
    });
});

