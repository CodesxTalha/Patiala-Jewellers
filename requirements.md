# Patiala Jewelers: Project Requirements

A small, calm, luxury showcase website for Patiala Jewelers (Gold & Diamonds, Islamabad). Visitors look at pieces and get in touch. They cannot buy online.

Visual rules live in `design.md`. This file says what the site contains and how it behaves.

## Goals
1. Make the brand feel premium and trustworthy within five seconds.
2. Let people browse pieces easily, mostly on a phone.
3. Turn browsing into a WhatsApp message, a call or a boutique visit.
4. Let the owner manage everything without a developer.

## Scope
**In:** browsing with filters, favorites, services, enquiry by WhatsApp or form, four boutiques with maps, admin panel, floating WhatsApp button, intro preloader.
**Out:** online buying, accounts, blog, reviews, live chat, multiple languages, imagery of people (product-only photography).

## Site map
```
Home
Collections ── Product page
Services ── Service page
Our Story
Contact (the four boutiques and the form)
Favorites
```
Header: Home, Collections, Services, Our Story; logo in the centre; icons for Favorites, Boutiques and Contact. On phones the logo is on the left, with icons and a slide-in menu on the right.

## Pages
- **Home:** hero film, collection tiles, selected pieces, services, Our Story band, boutiques.
- **Collections:** category links, metal filter, product grid with hover hearts, paging.
- **Product:** gallery, details, WhatsApp enquiry, save to favorites, enquiry form, related pieces.
- **Services:** photo cards. Each service page has a photo hero, description, what is included, steps, time and price, and a WhatsApp enquiry.
- **Our Story:** story text, photo, three promises, closing line.
- **Contact:** per-boutique details and small maps (each can open large), direct contact, message form.
- **Favorites:** pieces saved in the visitor's browser, with a "send my list on WhatsApp" link.

## Everything comes from the database
- **Store information:** name, tagline, contact, social links, colours, fonts, heading weight, logo, favicon, hero film, About text and photos.
- **Page text:** every line of page copy (Admin → Page text). **About values:** the three promises.
- **Catalogue:** categories, products with galleries, services, boutiques with coordinates.
- **Enquiries:** form messages with a status and notes.
Interface words (navigation, form labels, button names) are in the templates.

## Behaviour
- Smooth scrolling (Lenis); a scroll-linked header; the page is locked while the preloader shows (once per visit).
- Maps use MapLibre and free OpenFreeMap tiles. No API key, no paid service.
- Respects reduced-motion settings. Works without JavaScript for browsing and forms.

## Quality bar
No horizontal scroll from 320px to 1920px; readable contrast; fast images (lazy-loaded); WhatsApp link on every product and service.
