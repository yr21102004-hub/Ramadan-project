# UI/UX Professional Upgrade Logic

## Overview
We have visually upgraded the application to reflect a "Premium & Professional" brand identity suitable for a high-end Decor company.

## Changes Implemented

### 1. Visual Design System (`style.css`)
*   **Color Palette**: Refined the "Gold & Dark" theme.
    *   Dark backgrounds (`#0A0A0A`) for depth.
    *   Gold accents (`#D4AF37`) for luxury.
*   **Shadows**: Replaced flat shadows with multi-layered, smooth box-shadows for a 3D effect.
*   **Glassmorphism**: Enhanced the Navbar and Premium Cards with `backdrop-filter: blur(40px)` and subtle white borders.
*   **Typography**: Ensured 'Cairo' font is used consistently with optimized line heights.

### 2. Micro-Interactions
*   **Buttons**: Added a "click" scale effect (`transform: scale(0.96)`) to give tactile feedback.
*   **Hover Effects**: Cards now lift up (`translateY(-8px)`) with a glowing border on hover.
*   **Footer**: Links now slide slightly (`translateX`) and glow on hover.

### 3. Structural Updates
*   **Footer (`layout.html`)**: Rebuilt from scratch. Now features:
    *   Brand Column (Logo + Tagline + Socials).
    *   Quick Links.
    *   Services List.
    *   Contact Info with Icons.
*   **Homepage (`home.html`)**:
    *   **Stats Section**: Added a dynamic grid showing "30+ Years Experience", "100% Satisfaction", etc.
    *   **Why Choose Us**: Upgraded to "Premium Dark" theme with deep glassmorphism, animated golden borders, floating hover effects, and rotating icon rings.

### 4. Technical Details
*   **CSS Variables**: centralized in `:root` for easy maintenance.
*   **Responsive**: All new sections are grid-based and fully responsive.
*   **Performance**: Use of hardware-accelerated transitions (`transform`, `opacity`).
