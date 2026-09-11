# Prompt Canvas Design System

The generated image is the product. Everything here exists to present it and
get out of the way.

This document is the contract for PRD section 9. Every token below is defined
once in [`frontend/src/styles/tokens.css`](../frontend/src/styles/tokens.css)
and consumed through Tailwind utilities. **No component may hard-code a colour,
radius, shadow, duration, or type size.**

---

## 1. Design direction

Modern, focused, trustworthy, product-oriented.

**Deliberately absent**, per PRD 9.1:

| Not used | Why |
|---|---|
| Decorative gradients | They compete with the image for attention |
| Glassmorphism | Blur behind a photograph makes both harder to read |
| AI mascot illustration | Says nothing the interface does not already say |
| Multiple accent colours | The accent marks the primary action; a second one erases that meaning |

Warm dark is the default canvas: a brown-black ground with an amber accent, so
a generated image reads like a print on a warm wall rather than a card in a
bright dashboard. Light is a full peer theme -- a cream ground with the same
accent family -- and the viewer chooses.

Decorative secondaries (`plum`, `teal`, `violet`, `sun`) exist for gradient
meshes, stat pills, and feature-card icons. They are never used for a primary
action: that stays the single accent, which is what makes it findable.

---

## 2. Colour

Semantic names only. `--pc-danger`, never `--pc-red`, so a palette
change never requires renaming anything.

### Surfaces

| Token | Dark | Light | Use |
|---|---|---|---|
| `canvas` | `#0B0B0F` | `#F7F7F9` | The page |
| `surface` | `#16161C` | `#FFFFFF` | Panels, cards |
| `raised` | `#1E1E26` | `#FFFFFF` | Inputs, menus |
| `inset` | `#101015` | `#F0F0F3` | Wells, image mounts |
| `overlay` | `rgb(6 6 10 / .78)` | `rgb(23 23 28 / .5)` | Modal backdrop |

### Lines

| Token | Dark | Light |
|---|---|---|
| `line` | `#2A2A34` | `#E3E3E9` |
| `line-strong` | `#3A3A46` | `#CFCFD8` |

### Text

| Token | Dark | Contrast on canvas | Use |
|---|---|---|---|
| `ink` | `#E7E7EA` | 14.8:1 | Body, headings |
| `ink-secondary` | `#A1A1AC` | 7.4:1 | Supporting copy |
| `ink-muted` | `#7C7C88` | 4.6:1 | Metadata, counters |

All three clear WCAG AA for their sizes. `ink-muted` is reserved for text at
or above 12px that is never the only carrier of meaning.

### Accent

| Token | Dark | Light |
|---|---|---|
| `accent` | `#6366F1` | `#5457E5` |
| `accent-hover` | `#7C7FF3` | `#4245CF` |
| `accent-active` | `#4F52D9` | `#383BB8` |
| `accent-fg` | `#FFFFFF` | `#FFFFFF` |
| `focus` | `#A5B4FC` | `#4245CF` |

> **The accent rule.** One accent element per screen: the primary action.
> On the generator that is **Generate image**. On the result panel, Download is
> `secondary` — the image has already been produced, so downloading is no
> longer the thing the screen is for. If a second element wants the accent,
> the design is wrong, not the rule.

### Status

`success` `#34D399`, `warning` `#FBBF24`, `danger` `#F87171`, each with a
`-soft` background at 12–14% alpha for alert fills.

---

## 3. Typography

One family: **Inter**, with a full system fallback stack. The interface is not
the content.

| Step | Size | Use |
|---|---|---|
| `xs` | 12px | Metadata, character counter |
| `sm` | 13px | Labels, helper text, errors |
| `base` | 15px | Body, inputs, buttons |
| `lg` | 17px | Section headings |
| `xl` | 22px | Page headings |
| `2xl` | 28px | Hero heading |

Line height: `tight` 1.25 (headings), `normal` 1.55 (UI), `relaxed` 1.7
(prompts). Headings carry `-0.015em` tracking; uppercase metadata labels carry
`+0.04em`.

---

## 4. Spacing, radius, elevation

**Spacing** is Tailwind's 4px scale. Component padding uses 12/14/20/24px;
sections are separated by 24px, page regions by 32px.

**Radius:** `sm` 6px (focus ring, small chips) · `md` 10px (buttons, inputs) ·
`lg` 14px (image mount, alerts) · `xl` 20px (cards, dialogs).

**Elevation.** On a dark canvas a shadow alone reads as mud, so each level
pairs a shadow with a hairline top highlight (`--pc-ring-inset`).

| Level | Use |
|---|---|
| `sm` | Cards at rest, primary button |
| `md` | The generator panel |
| `lg` | Dialogs, toasts |

---

## 5. Motion

| Token | Duration | Use |
|---|---|---|
| `fast` | 120ms | Hover, focus, press |
| `base` | 200ms | Panel and disclosure transitions |
| `slow` | 360ms | Image fade-in, dialog entry |

Easing is `cubic-bezier(.2, 0, .15, 1)` throughout.

Under `prefers-reduced-motion: reduce`, durations collapse to 0.01ms rather
than being removed. A state change still happens — it just does not travel.

---

## 6. Iconography

A local inline set, [`components/ui/Icons.jsx`](../frontend/src/components/ui/Icons.jsx).
24px viewBox, 1.6 stroke, round caps and joins, `currentColor` fill. Rendered
at 14–18px. Every icon is `aria-hidden`; an icon-only control carries a
required `label` prop that becomes both `aria-label` and `title`.

---

## 7. Components

| Component | File |
|---|---|
| Button, IconButton | `ui/Button.jsx` |
| Field (label + hint + error) | `ui/Field.jsx` |
| TextInput, TextArea | `ui/TextInput.jsx`, `ui/TextArea.jsx` |
| SegmentedControl | `ui/SegmentedControl.jsx` |
| Card, CardHeader | `ui/Card.jsx` |
| Dialog | `ui/Dialog.jsx` |
| Alert | `ui/Alert.jsx` |
| Toast | `ui/Toast.jsx` |
| EmptyState | `ui/EmptyState.jsx` |
| Skeleton | `ui/Skeleton.jsx` |
| Spinner | `ui/Spinner.jsx` |

### Button variants

| Variant | Meaning |
|---|---|
| `primary` | The one accent action on the screen |
| `secondary` | Bordered. Everything else that is a real action |
| `ghost` | Tertiary. Dismiss, cancel, navigate |
| `danger` | Destructive. Distinct by border and text, not a red fill |

---

## 8. Component states (PRD 9.10)

Every interactive component implements all nine.

| State | How it is expressed |
|---|---|
| Default | Base token colours |
| Hover | One surface step lighter, or a stronger border |
| Focus | 2px `focus` outline, 2px offset — identical on every control |
| Active | `translate-y-px` plus the `-active` accent step |
| Disabled | 45% opacity, `cursor-not-allowed`, no hover response |
| Loading | Spinner replaces the leading icon, label swaps to a progressive verb, `aria-busy` set |
| Success | `success` token, `CheckIcon`, `role="status"` |
| Error | `danger` token, `AlertIcon`, `role="alert"` |
| Empty | `EmptyState` — never a blank box |

Focus is the same shape everywhere on purpose. A keyboard user learns it once.

---

## 9. Layout (PRD 9.3)

```
AppShell
├── Skip link          first tab stop on every page
├── Header             sticky, blurred, nav + theme + account
├── Main               max-width 84rem, id="main", tabIndex={-1}
│   ├── Generator      prompt, settings, submit
│   └── Result         empty | loading | success | error
└── Footer
```

| Breakpoint | Generator | History grid |
|---|---|---|
| `< 640px` | Stacked, form first | 1 column |
| `≥ 640px` | Stacked | 2 columns |
| `≥ 1024px` | Two columns, `26rem` form + fluid result | 3 columns |
| `≥ 1280px` | Two columns, wider gap | 4 columns |

The result mount reserves the aspect ratio of the **selected** size before an
image exists, so the layout never jumps when one arrives.

---

## 10. The four content states

**Empty** (9.5) — before the first generation the result area says
*"Your generated image will appear here"* and explains the next step. Never a
bare container.

**Loading** (9.6) — *"Generating image / Creating your visual."* The prompt and
every setting stay exactly as typed. The submit button disables, so a second
click cannot start a duplicate request. A previous result stays on screen at
25% opacity behind the overlay rather than being blanked.

**Error** (9.7) — the message appears next to the control that caused it, never
in a corner toast. Rate limiting shows beside the Generate button; generation
failures show under the result. Text is plain language with a retry. Raw
provider errors, HTTP bodies, and stack traces never reach the client — the
backend maps each provider failure to a fixed safe message and logs the
diagnostic separately.

**Success** — image, prompt, size, quality, model, file size, timestamp, and a
download action.

---

## 11. Accessibility (PRD 9.9)

- **Keyboard** — every action reachable; skip link first; `Ctrl`/`Cmd` + `Enter`
  submits from the prompt.
- **Focus** — always visible, one shape, 2px offset. Dialogs trap focus and
  return it to the trigger on close.
- **Labels** — every input has a real `<label htmlFor>`. Icon-only buttons
  require a `label` prop. Radio groups sit in a `<fieldset>` with a legend.
- **Alt text** — every generated image gets `Generated image: {prompt}`. Never
  empty, never "image".
- **Live regions** — the result mount is `aria-live="polite"` with `aria-busy`;
  errors are `role="alert"`; toasts are a polite live region.
- **Contrast** — all text meets AA in both themes.
- **Reduced motion** — respected globally.

---

## 12. UX principles (PRD 9.12)

1. **Minimise cognitive load.** Three inputs: prompt, size, quality.
2. **Keep the primary action obvious.** One accent element per screen.
3. **Feedback is immediate.** Every action moves to a visible state within one
   frame.
4. **Preserve input.** A failure never clears the prompt or the settings.
5. **Progressive disclosure.** The prompt guide is collapsed by default.
6. **Destructive actions are distinct.** Delete is the only `danger` control,
   and always behind a confirmation dialog naming the image.
7. **Plain language.** "Could not generate the image", not "502 Bad Gateway".
8. **Consistency.** One button, one field, one dialog, used everywhere.
