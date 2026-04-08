# Design System Specification: Neural Intelligence Framework

## 1. Overview & Creative North Star
**The Creative North Star: "The Obsidian Monolith"**

This design system moves beyond traditional dashboard utility into the realm of high-end, neural-inspired editorial design. We are not building a simple interface; we are crafting a sophisticated "Obsidian Monolith"—a digital environment that feels dense, powerful, and mysterious. 

To break the "standard template" look, this system rejects the rigid 12-column grid in favor of intentional asymmetry. Use large-scale typography that overlaps containers and wide-margin "breathing rooms" that suggest an infinite canvas. We prioritize depth through light rather than lines, using the "Crimson Glow" to draw the eye toward critical neural nodes.

---

## 2. Colors & Surface Philosophy

The color strategy is rooted in "Deep Obsidian" values. Our palette is a study in darkness, punctuated by a singular, aggressive high-energy accent.

### Palette Highlights
- **Primary (Crimson Glow):** `#ffb4aa` (Primary) to `#ff5545` (Container). This is the "heartbeat" of the system.
- **Surface (Deep Obsidian):** `#131313`. The base layer of the entire ecosystem.
- **Tertiary (Deep Gold):** `#e9c400`. Reserved strictly for secondary warnings or high-value insights.

### The "No-Line" Rule
**Prohibit 1px solid borders for sectioning.** Boundaries must be defined solely through background color shifts or tonal transitions.
- To separate a sidebar from a main feed, transition from `surface` to `surface-container-low`.
- To highlight a focused workspace, use `surface-bright`.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers—stacked sheets of obsidian glass.
- **Base Layer:** `surface` (#131313).
- **Secondary Workspace:** `surface-container` (#201f1f).
- **Interactive Nodes:** `surface-container-highest` (#353534).
*Instruction: Always nest containers by moving one tier up or down. Never place two containers of the same tier side-by-side.*

### The "Glass & Gradient" Rule
To achieve a signature, premium feel:
- **Glassmorphism:** All floating overlays (modals, dropdowns) must use `surface-container-low` with a 20px `backdrop-blur`.
- **The Crimson Pulse:** Main CTAs should not be flat. Use a linear gradient from `primary` (#ffb4aa) to `primary-container` (#ff5545) at a 135-degree angle.

---

## 3. Typography: Sharp & Modern

We use a dual-font strategy to balance high-tech precision with editorial authority.

- **Display & Headlines (Space Grotesk):** This is our "Precision" font. The geometric construction mirrors the neural network structure.
    - **Display-LG (3.5rem):** Use for system status or hero-level AI outputs.
    - **Headline-MD (1.75rem):** Used for section headers, often with increased letter spacing (0.05em).
- **Body & Titles (Manrope):** This is our "Clarity" font. It is highly readable and grounds the "mysterious" aesthetic in functional reality.
    - **Body-LG (1rem):** Default for user inputs and AI chat responses.
    - **Label-SM (0.6875rem):** Used for technical metadata.

*Director's Note: Use `on-surface-variant` (#e7bdb7) for secondary body text to maintain the low-contrast, sophisticated look while ensuring `on-surface` (#e5e2e1) is reserved for active, high-priority information.*

---

## 4. Elevation & Depth

### The Layering Principle
Depth is achieved through **Tonal Layering** rather than traditional structural lines.
- Place a `surface-container-lowest` card on a `surface-container-low` section to create a "recessed" look.
- Place a `surface-container-highest` card on a `surface` background to create a "protruding" look.

### Ambient Shadows & The Ghost Border
- **Shadows:** Use a "Crimson Ambient" shadow for active states. Use `primary` at 5% opacity with a 40px blur. 
- **Ghost Border Fallback:** If containment is required for accessibility, use the `outline-variant` token (#5d3f3b) at **15% opacity**. High-contrast, 100% opaque borders are strictly forbidden.

---

## 5. Component Logic

### Buttons (The "Power" Variant)
- **Primary:** Gradient fill (Primary to Primary-Container), white text (`on-primary`), `sm` (0.125rem) corner radius for a sharp, aggressive look.
- **Hover State:** Add a `0 0 15px` outer glow using the `primary` color.
- **Secondary:** Transparent background with a "Ghost Border."

### Neural Cards
- **Structure:** No dividers. Use 2rem of vertical padding between content blocks.
- **Interaction:** On hover, apply a subtle parallax shift (2-4px) and transition the background from `surface-container-low` to `surface-container-high`.
- **Accents:** A 2px wide vertical stripe of `primary` on the left edge indicates an "active" or "processing" state.

### Input Fields
- **State:** Resting state is a `surface-container-lowest` background with no border.
- **Focus State:** The container pulses with a subtle `primary` glow, and the label (Space Grotesk) shifts to `primary` color.

### Interactive Nodes (Specific to AI Context)
- **Pulse Indicator:** For "Thinking" states, use a radial gradient of `primary` that expands and fades behind the container.
- **Data Clusters:** Group related data using `surface-container-low` pods with `xl` (0.75rem) rounded corners to soften the "tech" edge.

---

## 6. Do’s and Don’ts

### Do:
- **Do** use asymmetrical layouts (e.g., a massive display-lg headline on the left with a small label-sm metadata block on the far right).
- **Do** lean into the "mysterious" tone by using high-contrast typography against low-contrast surface shifts.
- **Do** ensure all interactive elements have a "glow" transition on hover.

### Don't:
- **CRITICAL:** **Do not** reference port numbers, IP addresses, or low-level technical routing in the UI. Focus on the neural "Entity" or "Node" name.
- **Don't** use standard blue, green, or purple for success/info states. Use `secondary` (grey) for neutral info and `tertiary` (gold) for alerts.
- **Don't** use 1px dividers to separate list items. Use 16px of `surface-container` spacing instead.
- **Don't** use rounded corners larger than `xl` (0.75rem) except for buttons, which should remain `sm` (0.125rem) to stay "sharp."