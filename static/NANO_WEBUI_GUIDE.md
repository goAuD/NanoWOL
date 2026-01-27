# Nano WebUI CSS - Usage Guide

## Overview

`nano-webui.css` is the unified stylesheet for all Nano Product Family web interfaces. It provides:

- **CSS Custom Properties** (variables) for easy theming
- **Dark mode optimized** cyberpunk aesthetic
- **Reusable component classes** (buttons, cards, inputs, toasts)
- **Responsive utilities**
- **Animated grid background**

## Quick Start

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Nano App</title>
    
    <!-- Google Fonts (recommended) -->
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    
    <!-- Nano WebUI CSS -->
    <link rel="stylesheet" href="nano-webui.css">
</head>
<body class="nano-theme nano-grid-bg">
    <div class="nano-container">
        <h1 class="nano-logo nano-logo-xl nano-text-center">MyApp</h1>
        <p class="nano-subtitle nano-text-center nano-mb-lg">Nano Product Family</p>
        
        <div class="nano-card">
            <!-- Your content here -->
        </div>
        
        <footer class="nano-footer">
            <span class="nano-status-dot nano-status-dot-online"></span>
            MyApp v1.0.0 | Nano Product Family
        </footer>
    </div>
</body>
</html>
```

## CSS Variables

Override these in your own CSS to customize the theme:

```css
:root {
    /* Change accent color */
    --nano-cyan: #00ccff;
    
    /* Change background */
    --nano-bg-primary: #0d0d14;
}
```

### Available Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `--nano-bg-primary` | `#0a0a0f` | Main background |
| `--nano-bg-secondary` | `#12121a` | Secondary background |
| `--nano-bg-card` | `rgba(20, 20, 35, 0.8)` | Card background |
| `--nano-cyan` | `#00f0ff` | Primary accent |
| `--nano-magenta` | `#ff00aa` | Secondary accent |
| `--nano-green` | `#00ff88` | Success color |
| `--nano-red` | `#ff4466` | Danger color |
| `--nano-text-primary` | `#ffffff` | Main text |
| `--nano-text-secondary` | `#8892a0` | Muted text |

## Components

### Cards

```html
<div class="nano-card">
    <h2 class="nano-label">Section Title</h2>
    <p>Card content...</p>
</div>
```

### Buttons

```html
<!-- Default button -->
<button class="nano-btn">Click Me</button>

<!-- Variants -->
<button class="nano-btn nano-btn-success">Confirm</button>
<button class="nano-btn nano-btn-danger">Delete</button>
<button class="nano-btn nano-btn-primary">Submit</button>
```

### Inputs

```html
<input type="text" class="nano-input" placeholder="Enter value...">
<input type="checkbox" class="nano-checkbox">
```

### Toasts / Alerts

```html
<div class="nano-toast nano-toast-success">Operation successful!</div>
<div class="nano-toast nano-toast-error">An error occurred.</div>
<div class="nano-toast nano-toast-warning">Warning message.</div>
```

### Status Indicators

```html
<span class="nano-status-dot nano-status-dot-online"></span> Online
<span class="nano-status-dot nano-status-dot-offline"></span> Offline
```

## Utility Classes

### Layout

| Class | Description |
|-------|-------------|
| `nano-container` | Centered container (480px max) |
| `nano-container-lg` | Large container (800px max) |
| `nano-container-xl` | XL container (1200px max) |
| `nano-flex` | Flexbox container |
| `nano-flex-col` | Flex column direction |
| `nano-flex-center` | Center items |
| `nano-grid` | Grid container |
| `nano-grid-2` | 2 column grid |
| `nano-grid-3` | 3 column grid |

### Spacing

| Class | Description |
|-------|-------------|
| `nano-gap-sm` | 8px gap |
| `nano-gap-md` | 16px gap |
| `nano-gap-lg` | 24px gap |
| `nano-mb-sm` | 8px margin bottom |
| `nano-mb-md` | 16px margin bottom |
| `nano-mb-lg` | 24px margin bottom |

### Text

| Class | Description |
|-------|-------------|
| `nano-text-center` | Center align |
| `nano-text-left` | Left align |
| `nano-text-right` | Right align |

## Background Effects

Add `nano-grid-bg` to body for animated grid:

```html
<body class="nano-theme nano-grid-bg">
```

## Logo Styling

```html
<h1 class="nano-logo nano-logo-xl">AppName</h1>
<p class="nano-subtitle">Tagline here</p>
```

Sizes: `nano-logo-xl` (2.5rem), `nano-logo-lg` (2rem), `nano-logo-md` (1.5rem)

## Responsive Behavior

The stylesheet includes responsive breakpoints:

- Grid columns collapse to single column on mobile
- Buttons become full-width on mobile
- Logo font size reduces on smaller screens

## Integration with Existing Apps

If migrating an existing app, you can:

1. Include `nano-webui.css` first
2. Override specific variables in your app's CSS
3. Gradually replace existing classes with Nano classes

---

*Part of the Nano Product Family | Version 1.0.0*
