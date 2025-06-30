/**
 * HuntRED Design System - Theme Management
 * Unified theme handling for both React and Django templates
 */

// Theme constants
const THEMES = {
  LIGHT: 'light',
  DARK: 'dark'
};

// User roles
const ROLES = {
  CLIENT: 'client',
  CONSULTANT: 'consultant',
  ADMIN: 'admin',
  SUPERADMIN: 'superadmin'
};

// Theme management class
class ThemeManager {
  constructor() {
    this.currentTheme = localStorage.getItem('theme') || 
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? THEMES.DARK : THEMES.LIGHT);
    
    this.initialize();
  }

  initialize() {
    // Set initial theme
    this.applyTheme(this.currentTheme);
    
    // Setup event listeners
    document.addEventListener('DOMContentLoaded', () => {
      this.setupEventListeners();
    });
    
    // Listen for system theme changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      if (!localStorage.getItem('theme')) {
        this.applyTheme(e.matches ? THEMES.DARK : THEMES.LIGHT);
      }
    });
  }

  setupEventListeners() {
    // Find theme toggle button
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
      themeToggle.addEventListener('click', () => this.toggleTheme());
    }
  }

  applyTheme(theme) {
    this.currentTheme = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);

    // Update toggle button if it exists
    const themeIcon = document.getElementById('theme-icon');
    if (themeIcon) {
      themeIcon.className = theme === THEMES.DARK ? 
        'fas fa-sun text-yellow-300' : 
        'fas fa-moon text-gray-700';
    }

    // Dispatch custom event for React components and other JavaScript
    document.dispatchEvent(new CustomEvent('themeChanged', {
      detail: { theme: this.currentTheme }
    }));
  }

  toggleTheme() {
    const newTheme = this.currentTheme === THEMES.DARK ? THEMES.LIGHT : THEMES.DARK;
    this.applyTheme(newTheme);
  }

  // Apply role-specific styling
  applyRoleTheme(role) {
    document.documentElement.setAttribute('data-role', role);
  }
}

// Initialize theme manager
const themeManager = new ThemeManager();

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    themeManager,
    THEMES,
    ROLES
  };
}

// Make available globally
window.themeManager = themeManager;
