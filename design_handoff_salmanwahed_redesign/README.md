# Handoff: salmanwahed.com redesign

## Overview
A full visual redesign of **salmanwahed.com** (Django, two apps: `blog` and `portfolio`).
The goal is a sleek, modern, professional personal brand across six views:
Blog index, Post detail, Projects (professional + personal work), About, Resume, and Contact.

Two things are new versus the current site:
1. **Professional work** is showcased alongside personal projects (TallyKhata is the featured case study).
2. **Resume** and **Contact / Hire me** pages now exist, with `hello@salmanwahed.com` as the primary CTA.

## About the Design Files
`Salman Wahed.dc.html` is a **design reference created in HTML** — a prototype showing the intended
look and behavior. It is *not* production code and should not be copied into the repo. It is a single
self-contained page that fakes routing with client-side state so all six views can be clicked through.

**The task is to recreate this design inside the existing Django project**, using its established
patterns: template inheritance, `{% static %}`, existing URL names and views. The CSS in `css/`
*is* production-ready and can be dropped in more or less directly — see **Implementation Plan**.

## Fidelity
**High-fidelity.** Colors, typography, spacing, responsive behavior, and interaction states are final.
Recreate them faithfully. Where the prototype shows a striped `media-placeholder` box, that is a slot
for a real image the site owner will supply — keep the placeholder as a graceful fallback.

---

## Design Tokens

All tokens are CSS custom properties on `:root`, overridden under `[data-theme="dark"]`.
Never hardcode a hex value in a component — always reference the token.

### Color — light (default)
| Token | Value | Use |
|---|---|---|
| `--bg` | `#f2f5f6` | Page background (cool blue-grey paper) |
| `--bg-elev` | `#ffffff` | Cards, inputs, code blocks |
| `--ink` | `#131c24` | Primary text, headings |
| `--muted` | `#566673` | Body copy, descriptions |
| `--faint` | `#63707c` | Dates, eyebrows, form labels |
| `--border` | `#dde4e8` | All 1px rules and card borders |
| `--accent` | `#2f6fb0` | Solid buttons, badges, focus rings |
| `--accent-ink` | `#245486` | Accent-colored *text* and links (7.1:1 on `--bg`) |
| `--accent-soft` | `#dbe5ee` | Tinted chip/skill backgrounds |
| `--on-accent` | `#ffffff` | Text **on** a solid accent fill (5.2:1) |
| `--shadow` | `rgba(18,35,48,.07)` | Card shadow |

### Color — dark
| Token | Value |
|---|---|
| `--bg` | `#0d1317` |
| `--bg-elev` | `#151e24` |
| `--ink` | `#e6eef2` |
| `--muted` | `#94a4b1` |
| `--faint` | `#7b8b98` |
| `--border` | `#232f38` |
| `--accent` | `#2f6fb0` |
| `--accent-ink` | `#76a0cb` (6.8:1 on dark `--bg`) |
| `--accent-soft` | `#12202c` |
| `--on-accent` | `#ffffff` |
| `--shadow` | `rgba(0,0,0,.5)` |

> **Always use `color: var(--on-accent)` on accent-filled elements, never `color: #fff`.**
> The token exists so the foreground can flip if the accent is ever changed to a light hue.
> `base.css` includes a commented-out block if you want a brighter accent in dark mode.

### Typography
Three Google Fonts, one request:
```
https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&family=JetBrains+Mono:wght@400;500;600&display=swap
```

| Token | Family | Used for |
|---|---|---|
| `--font-sans` | **Manrope** 400/500/600/700 | Headings, nav, buttons, card titles |
| `--font-serif` | **Newsreader** 400/500/600 | Body copy, article text, form inputs |
| `--font-mono` | **JetBrains Mono** 400/500/600 | Eyebrows, dates, tags, code, monogram |

Type scale (desktop → ≤700px):
| Role | Desktop | Mobile | Weight | Line-height | Tracking |
|---|---|---|---|---|---|
| Blog hero h1 | 52 | 34 | 600 | 1.05 | -.025em |
| Page h1 (Projects/Contact) | 46 | 34 | 600 | 1.08 | -.025em |
| About h1 | 42 | 32 | 600 | 1.10 | -.025em |
| Post detail h1 | 40 | 30 | 600 | 1.12 | -.025em |
| Resume name | 38 | 38 | 600 | 1.15 | -.025em |
| Featured project h2 | 28 | 28 | 600 | 1.15 | -.02em |
| Post-body h2 | 25 | 25 | 600 | 1.15 | -.015em |
| Post list title | 24 | 20 | 600 | 1.25 | -.015em |
| Article body | 19 | 19 | 400 | 1.75 | — |
| Blog lede | 20 | 17 | 400 | 1.6 | — |
| Card body | 14.5–17 | same | 400 | 1.55–1.65 | — |
| Eyebrow (mono, caps) | 12 | 12 | 400 | — | .2em |
| Date / meta (mono) | 12.5–13 | same | 400 | — | — |
| Tag (mono) | 11.5 | 11.5 | 500 | 1.6 | — |

### Spacing, radius, shadow
- Container: `max-width: 1080px`, padding `0 var(--pad)` — **32px → 20px** at ≤700px
- Card padding: `var(--card-pad)` — **34px → 20px** at ≤700px
- Nav height: **74px**, sticky, `backdrop-filter: blur(14px)`
- Radius: `--radius-sm` 8px (chips) · `--radius` 12px (thumbs) · `--radius-lg` 18px (cards/forms) · `50rem` (tags) · `14px` (project cards, email link)
- Card shadow: `0 1px 0 var(--shadow)` — deliberately almost flat; depth comes from borders, not shadows
- Section rhythm: 64px top padding on page headers, 32px vertical padding per list row, 40–44px between major groups

---

## Responsive Behavior

**Verified at 320 / 360 / 414 / 768 / 909 / 1280px — zero horizontal overflow at every width.**

| Breakpoint | What changes |
|---|---|
| **≤992px** | Nav collapses to the hamburger dropdown. All dropdown targets get `min-height:44px`; the theme toggle and CTA go full-width. |
| **≤860px** | About and Contact grids → 1 column; `--gap-split` 56px → 38px |
| **≤780px** | Project grid → 1 column |
| **≤768px** | Post rows stack; thumbnail becomes full-width × 190px |
| **≤700px** | Type scale drops; `--pad` 32→20px; `--card-pad` 34→20px; **featured project card stacks vertically** and its logo goes 150→88px; resume date column unstacks; resume Skills/Education → 1 column |

Two responsive rules are load-bearing and are commented as such in the CSS — **do not remove them**:

1. **`.project-featured { flex-direction: column }` at ≤700px.** The body column uses `min-width:0`
   so it can shrink, which means it will *never* wrap on its own. Without the column direction, the
   logo and text stay side-by-side and the text is clipped (measured: 41px of content lost at 320px).
2. **`flex-wrap: wrap` on `.social-links` and `.footer ul`.** These mono uppercase link rows cannot
   break otherwise, and their min-content width becomes the grid column's automatic minimum — which
   pushed the Contact heading and lede off-screen at 320px.

Also note: **do not add `overflow-x: hidden` to the page wrapper.** It silently clips overflowing
content instead of fixing it, and it makes `documentElement.scrollWidth` report clean, hiding real
layout bugs from any automated check.

---

## Screens / Views

### 1. Blog index — `blog/index.html`
Landing page and article list; the site root.
**Layout:** Sticky nav → container → hero header (64px top padding, bottom-bordered) →
"LATEST WRITING" section label → vertical post list.
**Hero** — eyebrow (`--accent-ink`, mono caps), h1 capped at `18ch`, lede `--muted` capped at `60ch`.
**Post row** — flex, 34px gap, 32px vertical padding, 1px bottom border. Left: 210×140 thumbnail,
12px radius, `object-fit: cover`. Right: title → date/read-time → tag pills → excerpt.
Stacks below 768px. Whole row clickable; title turns `--accent-ink` on hover.

### 2. Post detail — `blog/post_detail.html`
Centered column, `max-width: 760px`. "← Back to blog" mono link → h1 → meta row → tag pills →
cover image at `clamp(180px, 42vw, 300px)` → `.post-body` at 19px/1.75 → author card.
**Body styles:** `h2` 25px, 40px top margin; `p` 24px bottom margin; `pre` on `--bg-elev` with
border + 10px radius; inline `code` on `--accent-soft`; `blockquote` with a 2px `--accent` left rule.

### 3. Projects — `portfolio/projects.html`
**The main new page.** Page header → "PROFESSIONAL WORK" label → featured card →
"OPEN SOURCE & PERSONAL APPS" label → 2-col card grid.
**Featured card** — elevated, 18px radius. Left: 150×150 logo. Right: badge row ("Featured" pill +
meta) → h2 → description capped at `62ch` → three stats → tech tags. **Stacks vertically at ≤700px.**
Duplicate this card for each additional professional role.
**Personal grid** — 2 cols → 1 col at 780px. Each card: 62px icon + title + description + tags.
Hover lifts 2px and borders turn accent. Content: SadaSidhe, TDS News, Alo Plus, History '71, Latest News.

### 4. About — `portfolio/about.html`
`1.4fr / 1fr` grid, collapses at 860px.
**Left:** eyebrow → h1 → three paragraphs (first `--ink`, rest `--muted`) → two buttons.
**Right:** 4:5 portrait (capped at 340px wide) → "Toolkit" card of skill chips.

### 5. Resume — `portfolio/resume.html`
Centered, `max-width: 840px`. Header: name + role + mono contact line, with a primary
"↓ Download PDF" button, above a bottom border. Sections: Summary → Experience → Skills / Education.
**Experience row:** 120px fixed mono date column + flexible content; stacks below 700px.
**Print:** a `@media print` block hides nav/footer/buttons and flattens to black-on-white, so
"Download PDF" can simply call `window.print()`. Or link a static PDF and keep the print CSS as a bonus.

### 6. Contact — `portfolio/contact.html`
2-col grid, collapses at 860px.
**Left:** eyebrow → h1 "Let's build something." → lede → large `.email-link` card
(mono "@" prefix, `hello@salmanwahed.com`) → mono uppercase social row.
**Right:** `.contact-form` card — mono uppercase labels, inputs that border-accent on focus,
full-width primary submit. Includes `.form-error` / `.form-success` for Django form feedback.

---

## Interactions & Behavior

- **Theme toggle** — flips `data-theme` on `<html>`, persists to `localStorage['sw-theme']`, falls
  back to `prefers-color-scheme` on first visit. Glyph ☾ in light, ☀ in dark. **An inline blocking
  script must run in `<head>` before the stylesheet** to prevent a flash — see `snippets/head.html`.
- **Nav** — sticky, translucent blurred background via `color-mix`. Below 992px it uses the CSS-only
  checkbox hamburger pattern (`input.nav-toggle:checked ~ .menu`), so the menu needs no JS.
- **Active nav link** — add `.is-active` to the current page's link (pass an `active` context var).
- **Transitions** — background/color on `body` 350ms; link and border colors 200ms; button hover
  lifts `translateY(-1px)` with `brightness(1.07)`.
- **Hover states** — post titles → `--accent-ink`; project cards → accent border + 2px lift;
  tags → tint deepens 12% → 20%; footer/social links → `--accent-ink`.
- **Touch targets** — everything interactive in the mobile dropdown is ≥44px.
- **Reduced motion** — a `prefers-reduced-motion` block near-zeroes transition/animation durations.
- **Focus** — inputs shift `border-color` to `--accent`. Consider adding a visible `:focus-visible`
  outline on buttons and links for keyboard users; the prototype does not include one.

## State Management
Minimal — server-rendered Django. The only client-side state:
- `theme`: `'light' | 'dark'`, in `localStorage['sw-theme']`, applied as `data-theme` on `<html>`.
- Mobile menu open/closed: pure CSS via a hidden checkbox, no JS.

Everything else comes from Django models and context.

---

## Implementation Plan

1. **Add the CSS.** Copy `css/base.css` into a shared static location, then:
   - `blog/static/blog/styles.css` ← `css/blog.css`
   - `portfolio/static/portfolio/styles.css` ← `css/portfolio.css`

   Both begin with `@import url("base.css")`. If that path is awkward, either fix the import, load
   `base.css` as a separate `<link>` before the app stylesheet, or concatenate at build time.
   **Do not duplicate the token block in both files** — it must stay single-source.

2. **Update the base template.** Add the inline theme script from `snippets/head.html` to `<head>`
   before the stylesheet; include `js/theme.js` before `</body>`. Wrap the page in `.wrapper` with
   `<main>` between the nav and footer partials. Make sure
   `<meta name="viewport" content="width=device-width, initial-scale=1">` is present.

3. **Rebuild nav and footer** from `snippets/_nav.html` and `snippets/_footer.html`. The markup
   differs from the current site: an inner wrapper div, a theme toggle, and a "Hire me" CTA.
   Fix the `{% url %}` names to match your URLconf.

4. **Restyle the blog templates** using `snippets/blog_index.html` as the markup reference —
   the post row now needs an `.img-wrapper` and a `.post-content` wrapper.

5. **Build the four portfolio views.** Projects likely needs a `Project` model with a `category`
   field (`professional` | `personal`) so the template can split the two groups. Resume entries are
   best modelled too, but hardcoding them in the template is fine for a personal site.

6. **Wire up Contact.** A Django `forms.Form` + view that emails `hello@salmanwahed.com`.
   Add a honeypot or rate limit — this address is published on the page.

7. **Tags.** The pill system expects `class="tag tag--{{ tag.slug }}"`. A palette is predefined for
   devops, sysadmin, python, flask, django, sqlalchemy, java, kotlin, android, engineering,
   programming — with brighter values under `[data-theme="dark"]`. Unknown slugs fall back to the
   accent, so no tag can break. If your `Tag` model stores a color, render
   `style="--tag: {{ tag.color }}"` instead and delete the modifier classes.

### Gotchas
- The old `a:hover { color: #448AFF !important; }` rule must be **deleted** — the `!important`
  overrides every accent color in the new system.
- `color-mix()` is used for tag tints and the nav's translucent background. Supported in all current
  evergreen browsers. For older support, replace tag rules with explicit `rgba()` and the nav
  background with a flat `var(--bg)`.
- There is a typo, `fon-weight`, in the `.date` rule of both original files. Fixed here.
- The old stylesheets duplicated ~150 lines across the two apps (nav, footer, body, pre, tags).
  That duplication is gone; it all lives in `base.css`.
- `.book-reports-list`, `.retrospective`, `.prev-next-links`, and `.gist` were carried over and
  restyled, so existing blog content keeps working.

## Assets
No image assets included — the prototype uses striped `.media-placeholder` boxes. You will need:
- **Post covers** — 210×140 in lists, up to 300px tall on detail pages
- **Project logos** — 150×150 for TallyKhata, 62×62 icons for personal apps
- **Portrait** — 4:5 for About
- **Avatar** — 38×38 in the nav (the "SW" monogram is a fine permanent choice)
- **Resume PDF** — if you prefer a real file over `window.print()`

Fonts are Google Fonts — free and open-source. Self-host with `@font-face` to avoid the third-party request.

## Files
| Path | What it is |
|---|---|
| `Salman Wahed.dc.html` | Interactive prototype — all six views, responsive, theme toggle. **Reference only.** |
| `css/base.css` | Tokens, reset, typography, nav, footer, tags, buttons. Shared. |
| `css/blog.css` | Blog app — post list, post detail, book reports, retrospectives. |
| `css/portfolio.css` | Portfolio app — projects, about, resume, contact. |
| `js/theme.js` | Theme toggle + persistence. |
| `snippets/head.html` | Inline anti-flash theme script for `<head>`. |
| `snippets/_nav.html` | Nav partial with theme toggle and Hire-me CTA. |
| `snippets/_footer.html` | Footer partial. |
| `snippets/blog_index.html` | Post-list markup reference. |
| `ORIGINAL_blog_styles.css` | Your current blog CSS, for diffing. |
| `ORIGINAL_portfolio_styles.css` | Your current portfolio CSS, for diffing. |
