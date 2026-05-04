---
name: Website Design System
description: Dimensional precision and aesthetic specifications for maintaining an "Institutional Editorial" professional configuration.
---

# Website Design System & Structural Specifications

To maintain a sophisticated "Institutional Editorial" aesthetic and ensure dimensional precision across the platform, the following architectural specifications must be strictly observed.

## 1. Primary Layout & Container Specifications
*   **Grid Framework:** All primary content must be encapsulated within the `::::: {.column-screen-inset .px-4}` wrapper.
*   **Spatial Constraints:** The global horizontal maximum width is restricted to `1320px` as defined in the core stylesheet. Individual page overrides are prohibited to maintain cross-platform uniformity.

## 2. Header Synchronization Protocols
*   **Cross-Page Continuity:** Graphical assets and primary body text must maintain a static horizontal and vertical position during navigational transitions between primary landing areas.
*   **Header Dimensionality:** To ensure this continuity, page-level headers must utilize identical vertical footprints:
    *   **Typography:** `Source Serif 4`, size `3.5rem`, weight `600`, line-height `1.1`.
    *   **Architecture:** Content must be encapsulated in a `<span>` within a `div` element utilizing a `border-bottom: 2px solid var(--border-color);`.
    *   **Padding and Margin:** Implement `padding-bottom: 0.5rem;` and `margin-bottom: 2rem;`.
*   **Horizontal Baseline Alignment:** Headers must be positioned external to the primary grid row to ensure precise alignment with the page container margin, thereby avoiding grid-induced indentation.

## 3. Primary Landing Configuration
*   **Vertical Padding:** The primary content grid must initiate with a standardized `padding-top: 0.5rem;` across all columns.
*   **Primary Graphical Asset:** 
    *   **Dimensions:** `max-width: 350px; aspect-ratio: 1 / 1;`.
    *   **Justification:** `text-align: right;` within the `g-col-lg-4` column.
    *   **Rendering:** Set to `display: block;` to eliminate descender-induced spacing anomalies.
*   **Navigational Modalities:** To ensure the inferior edge of the navigational boxes aligns with the inferior edge of the lead imagery:
    *   The text-containing column must utilize `display: flex; flex-direction: column; justify-content: space-between; height: 356px;`.
    *   **Spacing Parameters:** Textual blocks are restricted to `max-width: 700px`. Navigational elements must employ `justify-content: flex-start` with a `gap: 2rem` to adhere to the standardized left margin alignment.
    *   **Sectional Transitions:** Spacing between the primary landing configuration and subsequent content blocks must maintain a minimum of `.mt-5` to preserve structural cadence.

## 4. Typography & Visual Identity
*   **Case Consistency:** All primary headers must utilize **Title Case** formatting.
*   **Typeface Selection:** 
    *   Serif (Headings): `Source Serif 4` / `Fraunces`.
    *   Sans-Serif (Body/Navigation): `Inter` / `Plus Jakarta Sans`.
*   **Navigation Interface:** Branding elements within the navigation bar are suppressed globally via CSS to prioritize a minimalist interface.

## 5. Specialized Layout Frameworks
*   **Alignment Standards:** Headers must maintain left-justification and adhere to the typographic specifications of the primary landing areas.
*   **Structural Indentation:** Ensure titles remain external to the grid row to maintain a consistent horizontal baseline across all specialized pages.
*   **Vertical Sequential Prioritization:** For high-impact content, observe the following hierarchy: Full-width Title -> Full-width Graphical Asset -> Full-width Text. Vertical spacing must be strictly maintained at `margin-top: 0` for the header and `pt-2` for the container.
*   **Media Accumulation Rule:** Visual assets in multi-column configurations must be stacked vertically within their respective columns to ensure maximum clarity and a consistent vertical flow.

## 6. Authoritative Baseline Configuration
*   **System Integrity:** The platform is currently configured in an authoritative state regarding alignment, typography, and palette.
*   **Version Control Anchor:** Refer to the baseline commit for any necessary structural restoration.
*   **Palette Constraints:** The primary accent is restricted to **Oxblood Mahogany (`#7b341e`)** and the secondary background to **Warm Paper (`#faf9f8`)**. Modifications to this palette are not permitted without formal architectural review.

## Context / scope of the new skill
Maintaining high-end editorial aesthetics for web projects.

## Instructions
Refer to the structural specifications above for layout, header, and typography standards.

## Technical Crap
No special dependencies.

## Examples
See specifications in sections 1-6 above.

