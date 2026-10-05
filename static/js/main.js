/**
 * Smart Event Planning Platform - Main JavaScript Application
 * Handles global interactions, sidebar toggle, search shortcuts, and notifications.
 */

document.addEventListener('DOMContentLoaded', function () {
  // Mobile Sidebar Toggle
  const sidebar = document.querySelector('.app-sidebar');
  const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');

  if (sidebarToggleBtn && sidebar) {
    sidebarToggleBtn.addEventListener('click', function () {
      sidebar.classList.toggle('show-sidebar');
      if (sidebarBackdrop) {
        sidebarBackdrop.classList.toggle('d-none');
      }
    });
  }

  if (sidebarBackdrop && sidebar) {
    sidebarBackdrop.addEventListener('click', function () {
      sidebar.classList.remove('show-sidebar');
      sidebarBackdrop.classList.add('d-none');
    });
  }

  // Global Search Shortcut (Cmd+K / Ctrl+K)
  const globalSearchInput = document.getElementById('globalSearchInput');
  window.addEventListener('keydown', function (e) {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      if (globalSearchInput) {
        globalSearchInput.focus();
        globalSearchInput.select();
      }
    }
  });

  // Auto-dismiss Django Messages after 5 seconds
  const autoAlerts = document.querySelectorAll('.alert-dismissible');
  autoAlerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) {
        bsAlert.close();
      }
    }, 5000);
  });
});
