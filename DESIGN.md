# DESIGN SYSTEM SPECIFICATION
## Smart Event Planning Platform with Resource Coordination System
**Design Source:** Google Stitch Project `2231770233956563362` (*CampusOps Event Coordinator Platform / EventCore Platform*)

---

## 1. Brand Identity & Aesthetic Foundations
The visual theme targets operations managers, campus event coordinators, and enterprise logistics planners managing complex, high-stakes events across distributed spaces. The personality is **authoritative, calm under pressure, and methodically precise**.

- **Surfaces**: Cool, bright, low-glare canvas supporting sustained scheduling and conflict resolution.
- **Contrast**: Purposeful high-contrast alerts and active timeline markers on crisp, understated geometry.
- **Typography**: Inter / Poppins with JetBrains Mono for codes, timestamps, capacity, and monetary data.

---

## 2. Color System

### Primary & Core Brand Tokens
| Token Name | Hex Code | Usage |
| :--- | :--- | :--- |
| `primary` | `#1d4ed8` / `#0037b0` | Core interactive actions, active navigation states, primary timeline markers |
| `primary-hover` | `#1e40af` | Primary button hover |
| `primary-active` | `#1e3a8a` | Primary button active state |
| `primary-container` | `#1d4ed8` | Active navigation pill, key CTA buttons |
| `on-primary` | `#ffffff` | Text / icons on primary containers |
| `on-primary-container` | `#cad3ff` | Sub-labels on primary elements |
| `primary-fixed` | `#dce1ff` | Highlight tags, badges |
| `secondary` | `#0f172a` / `#565e74` | Structural headers, solid modals, typography |
| `secondary-container` | `#dae2fd` | Category chips, count badges |
| `tertiary` | `#004870` / `#0284c7` | Informational highlights, turnout lines, secondary indicators |
| `tertiary-container` | `#006194` / `#eff6ff` | Tertiary badges, icon containers |

### Surfaces & Canvas Backgrounds
| Token Name | Hex Code | Usage |
| :--- | :--- | :--- |
| `background` | `#f8f9ff` / `#f8fafc` | Global canvas background |
| `surface-container-lowest` | `#ffffff` | Pure white cards, tables, elevated containers |
| `surface-container-low` | `#eff4ff` / `#f1f5f9` | Input fields, table subheaders, badge containers |
| `surface-container` | `#e5eeff` / `#e2e8f0` | Progress bar tracks, dividers, inactive states |
| `surface-container-high` | `#dce9ff` | Subtle hover states, chip backgrounds |
| `surface-container-highest` | `#d3e4fe` | Elevated chip backgrounds |
| `outline` | `#747686` / `#64748b` | Sub-text, placeholder text, secondary icons |
| `outline-variant` | `#c4c5d7` / `#e2e8f0` | Structural borders, card borders, dividers |

### Semantic Status & Alert Colors
| State | Text & Icon | Background Container | Border Accent |
| :--- | :--- | :--- | :--- |
| **Confirmed / Success** | `#059669` (Emerald 600) | `#ecfdf5` (Emerald 50) | `#a7f3d0` (Emerald 200) |
| **Tentative / Warning** | `#d97706` (Amber 600) | `#fffbeb` (Amber 50) | `#fde68a` (Amber 200) |
| **Conflict / Error** | `#ba1a1a` / `#e11d48` (Rose 600) | `#ffdad6` / `#fff1f2` (Rose 50) | `#fecdd3` (Rose 200) |
| **Staged / Info** | `#2563eb` (Blue 600) | `#eff6ff` (Blue 50) | `#bfdbfe` (Blue 200) |

---

## 3. Typography Scale

The font family hierarchy uses **Poppins** & **Inter** for clean glyph readability, and **JetBrains Mono** for codes, dates, timestamps, room IDs, and financial amounts.

| Style Role | Font Family | Size | Weight | Line Height | Letter Spacing |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `display-lg` | Poppins / Inter | 32px (2.0rem) | 700 Bold | 40px | -0.02em |
| `headline-lg` | Poppins / Inter | 24px (1.5rem) | 600 SemiBold | 32px | -0.015em |
| `headline-md` | Poppins / Inter | 20px (1.25rem)| 600 SemiBold | 28px | -0.01em |
| `headline-sm` | Poppins / Inter | 16px (1.0rem) | 600 SemiBold | 24px | -0.005em |
| `body-lg` | Inter | 16px (1.0rem) | 400 Regular | 24px | 0 |
| `body-md` | Inter | 14px (0.875rem)| 400 Regular | 20px | 0 |
| `body-sm` | Inter | 12px (0.75rem)| 400 Regular | 16px | 0 |
| `label-md` | Poppins / Inter | 13px (0.8125rem)| 500 Medium | 16px | +0.01em |
| `label-sm` | Poppins / Inter | 11px (0.6875rem)| 600 SemiBold | 14px | +0.03em (Uppercase) |
| `data-mono` | JetBrains Mono | 12px (0.75rem)| 500 Medium | 16px | 0 |

---

## 4. Spacing & Architectural Rhythm

Built on an 8pt architectural grid with a 4pt sub-grid for dense controls:

- `space-xs`: `0.25rem` (4px)
- `space-sm`: `0.5rem` (8px)
- `space-md`: `0.75rem` (12px)
- `space-lg`: `1.0rem` (16px)
- `space-xl`: `1.5rem` (24px)
- `margin-lg`: `2.0rem` (32px)
- `gutter`: `1.0rem` (16px)
- `gutter-lg`: `1.5rem` (24px)

---

## 5. Border Radii & Elevation Hierarchy

### Border Radii
- **Input Controls & Small Buttons**: `0.5rem` (8px / `rounded-lg`)
- **Cards, Panels & Containers**: `1.0rem` (16px / `rounded-xl`)
- **Modals & Slide-overs**: `1.0rem` (16px / `rounded-xl`)
- **Pills, Badges & Avatars**: `9999px` (`rounded-full`)

### Elevation & Shadows
- **Base Canvas**: Zero elevation (`#f8f9ff`).
- **Standard Card / Container**: `border: 1px solid #e2e8f0; box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.05);`
- **Hover Card**: `box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.08), 0 2px 4px -2px rgba(15, 23, 42, 0.05);`
- **Floating Overlays & Dropdowns**: `box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.08);`
- **Modals**: `box-shadow: 0 20px 25px -5px rgba(15, 23, 42, 0.1), 0 8px 10px -6px rgba(15, 23, 42, 0.05);`

---

## 6. Button Styles
- **Primary Action**: Background `#1d4ed8`, text `#ffffff`, hover `#1e40af`, active `#1e3a8a`, padding `8px 16px`, height `38px` or `40px`, font `label-md`. Shadow: `0 1px 3px rgba(29, 78, 216, 0.2)`.
- **Secondary / Outline**: Background `#ffffff`, border `1px solid #e2e8f0`, text `#0f172a`, hover `#eff4ff`.
- **Destructive**: Background `#fff1f2`, border `1px solid #fecdd3`, text `#e11d48`, hover `#ffe4e6`.
- **Icon Action**: Width & height `34px` / `36px`, rounded `8px`, subtle hover background `#f1f5f9`.

---

## 7. Card & Container Styles
- Background `#ffffff`, border `1px solid #e2e8f0`, border radius `16px`.
- Dedicated header zones with subtle divider `1px solid #f1f5f9` or flex title + action alignment.
- Padding: `p-space-lg` (16px) or `p-space-xl` (24px).
- KPI Cards: Metric number in `display-lg`, trend indicator pill, category icon inside `w-10 h-10 rounded-lg bg-surface-container-low`.

---

## 8. Table Styles (High-Density Corporate)
- Header row: Background `#eff4ff` / `#f8fafc`, uppercase `label-sm`, tracking `0.03em`, text `#434655` / `#64748b`, height `40px`.
- Body rows: Alternating subtle hover `#f8f9ff`, border bottom `1px solid #f1f5f9`, row padding `12px 16px`.
- Selected/Active row: Background `#eff6ff` with a left border accent of `3px solid #1d4ed8`.
- Monospace codes: JetBrains Mono for Event IDs, Ticket IDs, Resource IDs, Budgets.

---

## 9. Form & Input Styles
- Height: `38px` – `40px`, border radius `8px` (`0.5rem`).
- Background: `#eff4ff` / `#f8fafc` or `#ffffff`, border `1px solid #cbd5e1`.
- Focus state: Border `#1d4ed8`, outline none, ring `0 0 0 3px rgba(29, 78, 216, 0.15)`.
- Label: Font `label-md` (13px, weight 500, color `#0b1c30`).
- Error state: Border `#e11d48`, ring `rgba(225, 29, 72, 0.15)`, helper text in `#e11d48`.

---

## 10. Responsive Behavior
- **Desktop (>= 1200px)**:
  - Persistent left sidebar: `260px` width.
  - Top header: fixed `left: 260px; right: 0; height: 64px`.
  - Main content: `margin-left: 260px; padding: 24px; max-width: 1720px`.
- **Tablet (768px - 1199px)**:
  - Sidebar toggles via backdrop overlay or off-canvas drawer.
  - Multi-column grids compress from 6 or 4 columns to 2 columns.
- **Mobile (< 768px)**:
  - Offcanvas hamburger navigation drawer.
  - Single column cards and horizontally scrolling tables.
  - Top bar with compact logo, search, and notification icon.

---

## 11. Reusable Components Extracted from Stitch Screens
1. **Sidebar Navigation Shell**: Brand logo, Campus Ops pill badge, active route pill (`bg-primary-container text-white`), badge counters, bottom user profile bar with avatar & logout.
2. **Top Navigation Bar**: Glassmorphism blur, breadcrumbs ("Operations > Campus Core"), campus selector pill, search bar with `⌘K` keyboard badge, primary CTA button ("+ New Event"), notifications bell with unread indicator, user profile quick menu.
3. **KPI Stat Card**: Title, icon bubble, large bold count, comparison trend indicator (`+12% vs last month`).
4. **Conflict Alert Banner / Card**: Rose border strip, warning icon, double-booking time interval in JetBrains Mono, "Resolve Conflict" & "Reassign Resource" buttons.
5. **Progress / Capacity Meter**: Bar with dynamic width, percentage, numeric count (e.g. `420 / 500 (84%)`).
6. **Status Badge / Chip**: Full rounded pill (`9999px`), dot indicator, uppercase text (`Confirmed`, `Draft`, `Conflict Pending`, `Cancelled`).
7. **Modal Shell**: Rounded 16px, backdrop blur, clean header with title and close icon, form grid, footer action buttons.
8. **Toast / Alert Dispatch**: Floating alert notifications for success, warning, and error messages.
