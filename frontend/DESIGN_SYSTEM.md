# ZaloPay Design System Documentation

## Overview

This design system provides a comprehensive set of design tokens, components, and guidelines to create consistent, pixel-perfect interfaces matching ZaloPay's official branding.

## Table of Contents

1. [Color Palette](#color-palette)
2. [Typography](#typography)
3. [Spacing System](#spacing-system)
4. [Components](#components)
5. [Layout Patterns](#layout-patterns)
6. [Usage Guidelines](#usage-guidelines)

---

## Color Palette

### Primary Colors

Our primary color palette is built around ZaloPay's signature blue, representing trust, technology, and innovation.

**ZaloPay Blue**
- `--zalopay-blue-primary`: #0068FF (Main brand color)
- `--zalopay-blue-dark`: #0052CC (Hover states, emphasis)
- `--zalopay-blue-light`: #3D8AFF (Highlights)
- `--zalopay-blue-lighter`: #E5F0FF (Backgrounds, badges)

**ZaloPay Green**
- `--zalopay-green`: #00C896 (Success, positive actions)
- `--zalopay-green-dark`: #00A078 (Hover states)
- `--zalopay-green-light`: #33D4A9 (Highlights)

### Accent Colors

**Orange** - `--zalopay-orange`: #FF6D3D (Promotions, calls-to-action)
**Purple** - `--zalopay-purple`: #7B61FF (Special features)
**Yellow** - `--zalopay-yellow`: #FFB800 (Warnings, highlights)

### Status Colors

- **Success**: #00C896 (Completed actions, confirmations)
- **Warning**: #FFB800 (Cautions, important notices)
- **Danger**: #FF3B30 (Errors, destructive actions)
- **Info**: #0068FF (Informational messages)

### Neutral Colors

Grayscale palette for text, backgrounds, and borders:

- `--color-gray-50`: #F9FAFB (Lightest background)
- `--color-gray-100`: #F3F4F6 (Light background)
- `--color-gray-200`: #E5E7EB (Borders, dividers)
- `--color-gray-300`: #D1D5DB
- `--color-gray-400`: #9CA3AF
- `--color-gray-500`: #6B7280 (Secondary text)
- `--color-gray-600`: #4B5563
- `--color-gray-700`: #374151
- `--color-gray-800`: #1F2937
- `--color-gray-900`: #111827 (Primary text)

### Gradients

Gradients add depth and visual interest:

```css
/* Primary Gradient - Blue to Green */
--gradient-primary: linear-gradient(135deg, #0068FF 0%, #00C896 100%);

/* Secondary Gradient - Purple to Blue */
--gradient-secondary: linear-gradient(135deg, #7B61FF 0%, #0068FF 100%);

/* Warm Gradient - Orange to Yellow */
--gradient-warm: linear-gradient(135deg, #FF6D3D 0%, #FFB800 100%);
```

---

## Typography

### Font Families

**Primary Font**: SF Pro Display (Apple's system font)
- Used for headings, UI elements, and body text
- Fallbacks: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial

**Secondary Font**: Inter
- Alternative for body text and UI components
- Excellent legibility at all sizes

**Monospace Font**: SF Mono
- Used for code snippets and technical data
- Fallbacks: Monaco, Cascadia Code, Roboto Mono

### Font Sizes

Mobile-first approach with rem units (1rem = 16px):

| Name | Variable | Size | Usage |
|------|----------|------|-------|
| XS | `--font-size-xs` | 0.75rem (12px) | Captions, labels |
| SM | `--font-size-sm` | 0.875rem (14px) | Small text, secondary info |
| Base | `--font-size-base` | 1rem (16px) | Body text |
| LG | `--font-size-lg` | 1.125rem (18px) | Emphasized text |
| XL | `--font-size-xl` | 1.25rem (20px) | Subheadings |
| 2XL | `--font-size-2xl` | 1.5rem (24px) | Section titles |
| 3XL | `--font-size-3xl` | 1.875rem (30px) | Page headings |
| 4XL | `--font-size-4xl` | 2.25rem (36px) | Major headings |
| 5XL | `--font-size-5xl` | 3rem (48px) | Hero text |
| 6XL | `--font-size-6xl` | 3.75rem (60px) | Display text |

### Font Weights

- **Light** (300): Rarely used, decorative text
- **Normal** (400): Body text
- **Medium** (500): Emphasized text
- **Semibold** (600): Subheadings, buttons
- **Bold** (700): Headings, important text
- **Extrabold** (800): Display text, hero sections

### Line Heights

- **Tight** (1.25): Headings, compact layouts
- **Snug** (1.375): Subheadings
- **Normal** (1.5): Body text (default)
- **Relaxed** (1.625): Long-form content
- **Loose** (2): Special emphasis, poetry

---

## Spacing System

### Base Unit: 8px

All spacing follows an 8-point grid system for visual rhythm and consistency.

| Variable | Value | Pixels | Usage |
|----------|-------|--------|-------|
| `--space-1` | 0.25rem | 4px | Tight spacing |
| `--space-2` | 0.5rem | 8px | Base unit |
| `--space-3` | 0.75rem | 12px | Small gaps |
| `--space-4` | 1rem | 16px | Standard gaps |
| `--space-5` | 1.25rem | 20px | Medium gaps |
| `--space-6` | 1.5rem | 24px | Large gaps |
| `--space-8` | 2rem | 32px | Section spacing |
| `--space-10` | 2.5rem | 40px | Large sections |
| `--space-12` | 3rem | 48px | Major sections |
| `--space-16` | 4rem | 64px | Hero sections |
| `--space-20` | 5rem | 80px | Page sections |
| `--space-24` | 6rem | 96px | Large sections |
| `--space-32` | 8rem | 128px | Extra large |

### Border Radius

Rounded corners for modern, friendly UI:

- `--radius-sm`: 0.25rem (4px) - Small elements
- `--radius-base`: 0.5rem (8px) - Default buttons, inputs
- `--radius-md`: 0.75rem (12px) - Cards
- `--radius-lg`: 1rem (16px) - Large cards
- `--radius-xl`: 1.5rem (24px) - Hero elements
- `--radius-2xl`: 2rem (32px) - Modals
- `--radius-full`: 9999px - Circular elements

### Shadows

Elevation system for depth hierarchy:

```css
--shadow-xs: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
--shadow-sm: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
--shadow-base: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
--shadow-md: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
--shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
--shadow-xl: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
--shadow-2xl: 0 35px 60px -15px rgba(0, 0, 0, 0.3);
```

---

## Components

### Buttons

#### Variants

**Primary**: Main actions, primary CTAs
```html
<button class="zp-btn zp-btn-primary">Get Started</button>
```

**Secondary**: Supporting actions
```html
<button class="zp-btn zp-btn-secondary">Learn More</button>
```

**Outline**: Tertiary actions
```html
<button class="zp-btn zp-btn-outline">Cancel</button>
```

**Ghost**: Minimal emphasis
```html
<button class="zp-btn zp-btn-ghost">Skip</button>
```

#### Sizes

- `zp-btn-sm`: Small buttons (forms, tables)
- `zp-btn`: Default size
- `zp-btn-lg`: Large buttons (landing pages)
- `zp-btn-xl`: Extra large (hero CTAs)

### Cards

Cards contain related content and actions:

```html
<div class="zp-card">
    <div class="zp-card-header">Card Title</div>
    <div class="zp-card-body">
        Card content goes here
    </div>
    <div class="zp-card-footer">
        <button class="zp-btn zp-btn-primary">Action</button>
    </div>
</div>
```

**Variants**: `zp-card-elevated`, `zp-card-gradient`, `zp-card-static`

### Forms

Form elements with consistent styling:

```html
<div class="zp-form-group">
    <label class="zp-form-label zp-form-label-required">Email</label>
    <input type="email" class="zp-form-control" placeholder="Enter your email">
    <span class="zp-form-help-text">We'll never share your email</span>
</div>
```

**States**: `zp-form-control-error`, `zp-form-control-success`

### Badges

Small status indicators:

```html
<span class="zp-badge zp-badge-success">Active</span>
<span class="zp-badge zp-badge-warning">Pending</span>
<span class="zp-badge zp-badge-danger">Error</span>
```

### Alerts

Contextual feedback messages:

```html
<div class="zp-alert zp-alert-success">
    <div class="zp-alert-icon">✓</div>
    <div class="zp-alert-content">
        <div class="zp-alert-title">Success!</div>
        Your changes have been saved.
    </div>
</div>
```

---

## Layout Patterns

### Header Navigation

Fixed header with logo, navigation links, and CTAs:

```html
<header class="zp-header">
    <div class="zp-header-container">
        <a href="/" class="zp-header-logo">
            <img src="/logo.png" alt="ZaloPay">
        </a>
        <nav class="zp-header-nav">
            <a href="#" class="zp-header-nav-link active">Home</a>
            <a href="#" class="zp-header-nav-link">Features</a>
            <a href="#" class="zp-header-nav-link">Pricing</a>
        </nav>
    </div>
</header>
```

### Hero Section

Eye-catching introductory section:

```html
<section class="zp-hero">
    <div class="zp-hero-container">
        <h1 class="zp-hero-title">Welcome to ZaloPay</h1>
        <p class="zp-hero-subtitle">Fast, secure, and easy payments</p>
        <div class="zp-hero-cta">
            <button class="zp-btn zp-btn-primary zp-btn-xl">Get Started</button>
            <button class="zp-btn zp-btn-outline zp-btn-xl">Learn More</button>
        </div>
    </div>
</section>
```

### Feature Grid

Showcase features in a responsive grid:

```html
<div class="zp-features-grid">
    <div class="zp-feature-card">
        <div class="zp-feature-icon">🚀</div>
        <h3 class="zp-feature-title">Fast Payments</h3>
        <p class="zp-feature-description">Process payments in seconds</p>
    </div>
    <!-- More feature cards -->
</div>
```

### Pricing Cards

Display pricing tiers:

```html
<div class="zp-pricing-grid">
    <div class="zp-pricing-card featured">
        <div class="zp-pricing-badge">Most Popular</div>
        <h3 class="zp-pricing-name">Pro</h3>
        <div class="zp-pricing-price">
            <span class="zp-pricing-amount">$29</span>
            <span class="zp-pricing-period">/month</span>
        </div>
        <ul class="zp-pricing-features">
            <li class="zp-pricing-feature">Unlimited transactions</li>
            <li class="zp-pricing-feature">24/7 Support</li>
        </ul>
        <button class="zp-btn zp-btn-primary w-full">Choose Plan</button>
    </div>
</div>
```

---

## Usage Guidelines

### Do's

✅ Use CSS variables for colors and spacing
✅ Follow the 8px spacing grid
✅ Use semantic HTML elements
✅ Ensure sufficient color contrast (WCAG AA minimum)
✅ Provide alt text for all images
✅ Test responsive layouts on mobile devices
✅ Use gradients sparingly for impact
✅ Maintain consistent button sizes within sections

### Don'ts

❌ Don't use hardcoded color values
❌ Don't use inline styles (use utility classes)
❌ Don't overuse `!important` declarations
❌ Don't mix spacing systems (stick to 8px grid)
❌ Don't create custom shadows (use design tokens)
❌ Don't ignore mobile breakpoints
❌ Don't use more than 2-3 colors in a single component

### Accessibility

- Maintain color contrast ratio of 4.5:1 for normal text
- Use semantic HTML (`<nav>`, `<main>`, `<article>`, etc.)
- Provide keyboard navigation for all interactive elements
- Include ARIA labels where appropriate
- Test with screen readers
- Ensure focus states are visible

### Responsive Design

Breakpoints:

- **SM**: 640px (Mobile landscape)
- **MD**: 768px (Tablet)
- **LG**: 1024px (Desktop)
- **XL**: 1280px (Large desktop)
- **2XL**: 1536px (Extra large)

Mobile-first approach - design for small screens first, then scale up.

---

## File Structure

```
frontend/css/
├── zalopay-variables.css    # Design tokens (colors, spacing, etc.)
├── zalopay-components.css   # Specific components (header, hero, etc.)
├── zalopay-shared.css       # Reusable components (buttons, cards, etc.)
├── merchant.css             # Merchant-specific styles
└── admin.css                # Admin-specific styles
```

### Import Order

In your HTML files:

```html
<!-- 1. Design tokens first -->
<link rel="stylesheet" href="/css/zalopay-variables.css">

<!-- 2. Shared components -->
<link rel="stylesheet" href="/css/zalopay-shared.css">

<!-- 3. Specific components -->
<link rel="stylesheet" href="/css/zalopay-components.css">

<!-- 4. Page-specific styles -->
<link rel="stylesheet" href="/css/merchant.css">
```

---

## Resources

- **ZaloPay Official**: https://zalopay.vn
- **Merchant Portal**: https://mc.zalopay.vn
- **Color Contrast Checker**: https://webaim.org/resources/contrastchecker/
- **Responsive Design Testing**: Use browser DevTools

---

## Version History

- **v1.0.0** (2025-10-21): Initial design system release
  - Complete color palette
  - Typography system
  - Spacing tokens
  - Core components
  - Layout patterns

---

## Support

For questions or suggestions about this design system:
- Review the code in `frontend/css/`
- Check examples in HTML files
- Run design audit: `python3 scripts/design_audit.py`
