# 🛡️ FORENSIGHT Enterprise Brand Identity Suite

> [!NOTE]
> **Design Language**: Minimal · Professional · Enterprise · Cybersecurity · DFIR · Artificial Intelligence
> **Color System**: White (`#FFFFFF`), Electric Blue (`#18A0FB`), Dark Navy (`#081320`)
> **Format**: 100% Scalable Editable Vectors & Text (Zero Raster Graphics)

---

## 🎨 1. Primary Logo (Horizontal Master Brandmark)

*Used on primary enterprise headers, official documentation, web portals, and software headers.*

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 120" width="100%" height="120" style="background:#081320; border-radius:12px;">
  <defs>
    <linearGradient id="electricBlueGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#18A0FB"/>
      <stop offset="100%" stop-color="#0066FF"/>
    </linearGradient>
  </defs>

  <g transform="translate(30, 25)">
    <!-- Brand Icon -->
    <g transform="translate(0, 5)">
      <!-- Shield Outer Contour -->
      <path d="M 28 0 L 56 10 V 30 C 56 46 44 60 28 66 C 12 60 0 46 0 30 V 10 L 28 0 Z" fill="none" stroke="#18A0FB" stroke-width="3.5" stroke-linejoin="round"/>
      <!-- Digital Reticle / AI Core -->
      <circle cx="28" cy="28" r="12" fill="none" stroke="#ffffff" stroke-width="2.5" stroke-dasharray="6 3"/>
      <circle cx="28" cy="28" r="4.5" fill="#18A0FB"/>
      <!-- Node Trace Points -->
      <circle cx="28" cy="6" r="2" fill="#18A0FB"/>
      <circle cx="50" cy="28" r="2" fill="#18A0FB"/>
      <circle cx="6" cy="28" r="2" fill="#18A0FB"/>
    </g>

    <!-- Wordmark -->
    <g transform="translate(75, 12)">
      <!-- FORE -->
      <text x="0" y="34" fill="#FFFFFF" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="34" font-weight="900" letter-spacing="3">FORE</text>
      <!-- Stylized E Triple Bars -->
      <g transform="translate(92, 9)">
        <rect x="0" y="0" width="18" height="4.5" fill="#FFFFFF" rx="1"/>
        <rect x="0" y="9.5" width="15" height="4.5" fill="#FFFFFF" rx="1"/>
        <rect x="0" y="19" width="18" height="4.5" fill="#FFFFFF" rx="1"/>
      </g>
      <!-- NSIGHT -->
      <text x="116" y="34" fill="url(#electricBlueGrad)" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="34" font-weight="900" letter-spacing="3">NSIGHT</text>

      <!-- Underline Trace with Node Terminal -->
      <line x1="0" y1="46" x2="260" y2="46" stroke="#18A0FB" stroke-width="2" stroke-linecap="round"/>
      <circle cx="268" cy="46" r="3" fill="#18A0FB"/>
      <circle cx="277" cy="46" r="4.5" fill="none" stroke="#18A0FB" stroke-width="2"/>
    </g>
  </g>
</svg>
```

---

## 🏛️ 2. Secondary Logo (Stacked Center Lockup)

*Used for splash screens, official security certifications, login cards, and presentation title slides.*

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 200" width="100%" height="200" style="background:#081320; border-radius:12px;">
  <g transform="translate(200, 35)" text-anchor="middle">
    <!-- Icon -->
    <g transform="translate(-28, 0)">
      <path d="M 28 0 L 56 10 V 30 C 56 46 44 60 28 66 C 12 60 0 46 0 30 V 10 L 28 0 Z" fill="none" stroke="#18A0FB" stroke-width="3.5" stroke-linejoin="round"/>
      <circle cx="28" cy="28" r="12" fill="none" stroke="#ffffff" stroke-width="2.5" stroke-dasharray="6 3"/>
      <circle cx="28" cy="28" r="4.5" fill="#18A0FB"/>
    </g>

    <!-- Wordmark -->
    <text x="0" y="105" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="28" font-weight="900" letter-spacing="4">
      <tspan fill="#FFFFFF">FORE</tspan>
      <tspan fill="#18A0FB">NSIGHT</tspan>
    </text>

    <!-- Tagline -->
    <text x="0" y="132" fill="#94A3B8" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="10" font-weight="700" letter-spacing="3">
      DIGITAL FORENSICS &amp; INCIDENT RESPONSE
    </text>
  </g>
</svg>
```

---

## 🎯 3. Icon Only (Standalone Symbol)

*Used as navigation bar brand mark, avatar badge, or product stamp.*

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120" width="120" height="120" style="background:#081320; border-radius:16px;">
  <g transform="translate(32, 27)">
    <path d="M 28 0 L 56 10 V 30 C 56 46 44 60 28 66 C 12 60 0 46 0 30 V 10 L 28 0 Z" fill="none" stroke="#18A0FB" stroke-width="4" stroke-linejoin="round"/>
    <circle cx="28" cy="28" r="13" fill="none" stroke="#ffffff" stroke-width="3" stroke-dasharray="6 3"/>
    <circle cx="28" cy="28" r="5" fill="#18A0FB"/>
    <circle cx="28" cy="6" r="2.5" fill="#18A0FB"/>
    <circle cx="50" cy="28" r="2.5" fill="#18A0FB"/>
    <circle cx="6" cy="28" r="2.5" fill="#18A0FB"/>
  </g>
</svg>
```

---

## 📱 4. App Icon (Mobile & Desktop Application Tile)

*Used for macOS / iOS / Windows desktop app launchers.*

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180 180" width="140" height="140">
  <defs>
    <linearGradient id="appBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0F172A"/>
      <stop offset="100%" stop-color="#081320"/>
    </linearGradient>
    <linearGradient id="iconGlow" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#18A0FB"/>
      <stop offset="100%" stop-color="#0066FF"/>
    </linearGradient>
  </defs>

  <!-- Squircle Base -->
  <rect x="0" y="0" width="180" height="180" rx="40" fill="url(#appBg)" stroke="rgba(24, 160, 251, 0.3)" stroke-width="2"/>

  <!-- Shield Core -->
  <g transform="translate(62, 50)">
    <path d="M 28 0 L 56 10 V 30 C 56 46 44 60 28 66 C 12 60 0 46 0 30 V 10 L 28 0 Z" fill="none" stroke="url(#iconGlow)" stroke-width="4.5" stroke-linejoin="round"/>
    <circle cx="28" cy="28" r="13" fill="none" stroke="#FFFFFF" stroke-width="3" stroke-dasharray="6 3"/>
    <circle cx="28" cy="28" r="5" fill="#18A0FB"/>
  </g>
</svg>
```

---

## 🔖 5. Favicon (Browser Tab Icon - 32x32 Viewport)

*Optimized for extreme crispness at 16x16 and 32x32 browser tab scale.*

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
  <rect width="32" height="32" rx="6" fill="#081320"/>
  <path d="M 16 4 L 26 8 V 16 C 26 22 20 26 16 28 C 12 26 6 22 6 16 V 8 L 16 4 Z" fill="none" stroke="#18A0FB" stroke-width="2.2"/>
  <circle cx="16" cy="15" r="3.5" fill="#FFFFFF"/>
</svg>
```

---

## ☀️ 6. Light Theme Version

*Used on white reports, PDF evidence downloads, and light-background executive summaries.*

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 120" width="100%" height="120" style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:12px;">
  <g transform="translate(30, 25)">
    <g transform="translate(0, 5)">
      <path d="M 28 0 L 56 10 V 30 C 56 46 44 60 28 66 C 12 60 0 46 0 30 V 10 L 28 0 Z" fill="none" stroke="#18A0FB" stroke-width="3.5" stroke-linejoin="round"/>
      <circle cx="28" cy="28" r="12" fill="none" stroke="#081320" stroke-width="2.5" stroke-dasharray="6 3"/>
      <circle cx="28" cy="28" r="4.5" fill="#18A0FB"/>
    </g>

    <g transform="translate(75, 12)">
      <text x="0" y="34" fill="#081320" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="34" font-weight="900" letter-spacing="3">FORE</text>
      <text x="116" y="34" fill="#18A0FB" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="34" font-weight="900" letter-spacing="3">NSIGHT</text>

      <line x1="0" y1="46" x2="260" y2="46" stroke="#18A0FB" stroke-width="2" stroke-linecap="round"/>
      <circle cx="268" cy="46" r="3" fill="#18A0FB"/>
      <circle cx="277" cy="46" r="4.5" fill="none" stroke="#18A0FB" stroke-width="2"/>
    </g>
  </g>
</svg>
```

---

## 🌙 7. Dark Theme Version

*Used on dark SOC dashboards, dark mode web applications, and cyber command centers.*

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 120" width="100%" height="120" style="background:#081320; border:1px solid #1E293B; border-radius:12px;">
  <g transform="translate(30, 25)">
    <g transform="translate(0, 5)">
      <path d="M 28 0 L 56 10 V 30 C 56 46 44 60 28 66 C 12 60 0 46 0 30 V 10 L 28 0 Z" fill="none" stroke="#18A0FB" stroke-width="3.5" stroke-linejoin="round"/>
      <circle cx="28" cy="28" r="12" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-dasharray="6 3"/>
      <circle cx="28" cy="28" r="4.5" fill="#18A0FB"/>
    </g>

    <g transform="translate(75, 12)">
      <text x="0" y="34" fill="#FFFFFF" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="34" font-weight="900" letter-spacing="3">FORE</text>
      <text x="116" y="34" fill="#18A0FB" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="34" font-weight="900" letter-spacing="3">NSIGHT</text>

      <line x1="0" y1="46" x2="260" y2="46" stroke="#18A0FB" stroke-width="2" stroke-linecap="round"/>
      <circle cx="268" cy="46" r="3" fill="#18A0FB"/>
      <circle cx="277" cy="46" r="4.5" fill="none" stroke="#18A0FB" stroke-width="2"/>
    </g>
  </g>
</svg>
```

---

## 🖤 8. Black & White Version (Monochrome)

*Used for laser engraving, single-color print, faxing, and high-security court documents.*

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 120" width="100%" height="120" style="background:#FFFFFF; border:1px solid #000000; border-radius:12px;">
  <g transform="translate(30, 25)">
    <g transform="translate(0, 5)">
      <path d="M 28 0 L 56 10 V 30 C 56 46 44 60 28 66 C 12 60 0 46 0 30 V 10 L 28 0 Z" fill="none" stroke="#000000" stroke-width="4" stroke-linejoin="round"/>
      <circle cx="28" cy="28" r="12" fill="none" stroke="#000000" stroke-width="2.5" stroke-dasharray="6 3"/>
      <circle cx="28" cy="28" r="4.5" fill="#000000"/>
    </g>

    <g transform="translate(75, 12)">
      <text x="0" y="34" fill="#000000" font-family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif" font-size="34" font-weight="900" letter-spacing="3">FORENSIGHT</text>

      <line x1="0" y1="46" x2="260" y2="46" stroke="#000000" stroke-width="2.5" stroke-linecap="round"/>
      <circle cx="268" cy="46" r="3" fill="#000000"/>
      <circle cx="277" cy="46" r="4.5" fill="none" stroke="#000000" stroke-width="2"/>
    </g>
  </g>
</svg>
```

---

## 🌐 9. Social Media Profile Avatar (400x400 Square)

*Used for LinkedIn, GitHub, Twitter/X, and YouTube organization avatars.*

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 400" width="200" height="200">
  <rect width="400" height="400" fill="#081320"/>
  <circle cx="200" cy="200" r="180" fill="none" stroke="rgba(24, 160, 251, 0.15)" stroke-width="2"/>

  <!-- Centered Master Icon -->
  <g transform="translate(144, 125)">
    <path d="M 56 0 L 112 20 V 60 C 112 92 88 120 56 132 C 24 120 0 92 0 60 V 20 L 56 0 Z" fill="none" stroke="#18A0FB" stroke-width="7" stroke-linejoin="round"/>
    <circle cx="56" cy="56" r="26" fill="none" stroke="#FFFFFF" stroke-width="5" stroke-dasharray="12 6"/>
    <circle cx="56" cy="56" r="10" fill="#18A0FB"/>
  </g>
</svg>
```

---

## 💳 10. Business Card Preview (Front & Back Vector Layout)

*Professional 3.5" x 2.0" executive business card design.*

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 700 420" width="100%" height="420" style="background:#0B0F19; border-radius:16px; padding:20px;">
  <!-- FRONT OF CARD -->
  <g transform="translate(30, 40)">
    <rect width="300" height="170" rx="12" fill="#081320" stroke="#1E293B" stroke-width="2"/>
    <!-- Minimal Brand Center -->
    <g transform="translate(45, 60)">
      <path d="M 16 0 L 32 6 V 18 C 32 27 25 36 16 39 C 7 36 0 27 0 18 V 6 L 16 0 Z" fill="none" stroke="#18A0FB" stroke-width="2.5"/>
      <circle cx="16" cy="16" r="6" fill="none" stroke="#FFFFFF" stroke-width="1.5" stroke-dasharray="3 2"/>
      <circle cx="16" cy="16" r="2.5" fill="#18A0FB"/>
      <text x="42" y="24" fill="#FFFFFF" font-family="-apple-system, sans-serif" font-size="16" font-weight="900" letter-spacing="2">FORE<tspan fill="#18A0FB">NSIGHT</tspan></text>
    </g>
    <text x="150" y="140" fill="#94A3B8" font-family="-apple-system, sans-serif" font-size="7" font-weight="700" letter-spacing="2" text-anchor="middle">WWW.FORENSIGHT.AI</text>
  </g>

  <!-- BACK OF CARD -->
  <g transform="translate(370, 40)">
    <rect width="300" height="170" rx="12" fill="#081320" stroke="#1E293B" stroke-width="2"/>
    <g transform="translate(30, 35)">
      <text x="0" y="20" fill="#FFFFFF" font-family="-apple-system, sans-serif" font-size="14" font-weight="800">ALEX JENSEN</text>
      <text x="0" y="34" fill="#18A0FB" font-family="-apple-system, sans-serif" font-size="8" font-weight="700" letter-spacing="1">CHIEF FORENSIC INVESTIGATOR</text>
      
      <line x1="0" y1="46" x2="240" y2="46" stroke="#1E293B" stroke-width="1"/>

      <text x="0" y="65" fill="#94A3B8" font-family="-apple-system, sans-serif" font-size="8">E: alex.jensen@forensight.ai</text>
      <text x="0" y="80" fill="#94A3B8" font-family="-apple-system, sans-serif" font-size="8">P: +1 (800) 555-DFIR</text>
      <text x="0" y="95" fill="#94A3B8" font-family="-apple-system, sans-serif" font-size="8">A: 100 Cyber Defense Plaza, Suite 400</text>
    </g>
  </g>
</svg>
```

---

## 🎨 Enterprise Palette Tokens

| Role | Color Name | Hex Code | Usage |
| :--- | :--- | :--- | :--- |
| **Primary Accent** | Electric Blue | `#18A0FB` | Reticle core, cyan text, active node traces, primary CTA buttons |
| **Background / Container** | Dark Navy | `#081320` | SOC dashboard panels, dark headers, card containers |
| **High Contrast Text** | Pure White | `#FFFFFF` | Primary headers, wordmark prefix, crisp vector elements |
| **Secondary Neutral** | Cool Slate | `#94A3B8` | Taglines, secondary metadata, border strokes |
