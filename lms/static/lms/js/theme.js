(function () {
    "use strict";

    var root = document.documentElement;
    var STORAGE_KEY = "sematec-lms-theme";

    function applyTheme(theme) {
        if (theme === "dark") {
            root.setAttribute("data-theme", "dark");
        } else {
            root.removeAttribute("data-theme");
        }
        updateToggleIcon(theme);
    }

    function updateToggleIcon(theme) {
        var icon = document.getElementById("theme-toggle-icon");
        if (!icon) return;
        icon.className = theme === "dark" ? "bi bi-sun" : "bi bi-moon-stars";
    }

    function currentTheme() {
        return root.getAttribute("data-theme") === "dark" ? "dark" : "light";
    }

    // Apply saved (or system) preference as early as possible.
    var saved = localStorage.getItem(STORAGE_KEY);
    if (!saved) {
        saved = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    applyTheme(saved);

    document.addEventListener("DOMContentLoaded", function () {
        updateToggleIcon(currentTheme());

        var toggleBtn = document.getElementById("theme-toggle");
        if (toggleBtn) {
            toggleBtn.addEventListener("click", function () {
                var next = currentTheme() === "dark" ? "light" : "dark";
                applyTheme(next);
                localStorage.setItem(STORAGE_KEY, next);
            });
        }

        var sidebarToggle = document.getElementById("sidebar-toggle");
        var sidebar = document.querySelector(".sidebar");
        if (sidebarToggle && sidebar) {
            sidebarToggle.addEventListener("click", function () {
                sidebar.classList.toggle("open");
            });

            document.addEventListener("click", function (event) {
                if (window.innerWidth > 991) return;
                if (!sidebar.classList.contains("open")) return;
                if (sidebar.contains(event.target) || sidebarToggle.contains(event.target)) return;
                sidebar.classList.remove("open");
            });
        }
    });
})();
