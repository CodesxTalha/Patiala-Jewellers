# Patiala Jewelers Design Guide

Use this file as the source of truth for every design made for Patiala Jewelers (visiting cards, social posts, packaging, website, stationery, signage). Follow it exactly. If something is not covered here, choose the simplest, calmest, most restrained option.

## Brand

Name: Patiala Jewelers
Short name: Patiala
Descriptor: Gold & Diamonds
Monogram: PJ with a small crown (logo file is provided separately; never redraw or alter it)
Website: patialajewelersofficial.com
Locations (Islamabad): PWD, DHA II, Ghauri Town, F-7
Personality: premium, luxury, calm, timeless, confident. Quiet luxury, never loud.
Spelling: always "Jewelers" (one L before the E), never "Jewllers".

## Colours

Use only these colours. Flat fills only. No gradients, no shadows, no textures, no glow effects.

Gold (main brand colour): #B8975A
Soft Black: #161513
Soft White: #FAF8F3

Helper colours
Light Gold: #C9A96A (gold on dark backgrounds only)
Deep Gold: #8A6D35 (small gold text on light backgrounds)
Warm Grey: #6A6458 (secondary text on light backgrounds)
Cream: #F3EFE6 (text on dark backgrounds)

Rules
- Never use pure black #000000 or pure white #FFFFFF.
- Proportion: about 60 percent Soft White, 30 percent Soft Black, 10 percent Gold. Gold is an accent, not a fill.
- Gold is for the logo, monogram, thin lines and small labels. Never for paragraphs or large areas.
- Light backgrounds: gold shapes use #B8975A, small gold text uses #8A6D35.
- Dark backgrounds: gold uses #C9A96A.
- Every design pairs one light surface and one dark surface where it has two sides or two sections.

## Typography

Two fonts only, both free on Google Fonts.

Playfair Display, Regular 400: brand name, names of people and headings.
Montserrat, Light 300: everything else (details, labels, body text, captions).

Styles
- Brand name: PATIALA in Playfair Display Regular, capitals, letter-spacing 30 to 34 percent.
- Descriptor: JEWELERS in Montserrat Light, capitals, letter-spacing about 40 percent, gold (Deep Gold on light, Light Gold on dark).
- Headings and names: Playfair Display Regular, normal case, no letter-spacing.
- Labels: Montserrat Light, capitals, wide letter-spacing (30 to 45 percent).
- Details and body: Montserrat Light, normal case, letter-spacing about 5 percent, line height 1.6.

Rules
- Never use bold. Never use italic except for a rare quote in Playfair Display.
- Light text is always Soft Black or Warm Grey on light surfaces, Cream on dark surfaces. Never thin gold text for anything small.
- For print, the smallest text is 6 pt. If Light looks too faint at small sizes, increase the size before changing the weight.

## Logo

- Primary lockup: PJ monogram above PATIALA, then JEWELERS between two thin gold lines, then GOLD & DIAMONDS in small spaced capitals.
- The monogram is gold on dark, gold on light. Nothing else.
- Keep clear space around the logo equal to the height of the letter A in PATIALA.
- Never stretch, rotate, outline, recolour, add effects or change the typeface.
- Never place the logo on a busy or low-contrast background.

## Layout

- Calm and spacious. Fewer elements is better. If a layout feels full, remove something.
- Generous margins: at least 7 percent of the shortest side.
- Align to a clear grid. Everything either centred on one axis or left-aligned on one edge. Never scatter elements.
- Thin gold lines (1 to 1.5 px, or 0.15 mm in print) as dividers. Square corners only.
- Brand first: the brand name or monogram is always the strongest element. People names are smaller than the brand.
- Use plenty of empty space; do not fill it.

## Photography and imagery

- Close, soft, warm product photography. One piece per frame.
- Backgrounds: Soft Black, Soft White or warm neutral tones.
- No harsh flash, no busy backgrounds, no heavy filters, no text over the jewellery.

## Visiting card

Size: 90 x 50 mm (design at 840 x 480 px), landscape. Safe margin 5 mm from every edge, add 3 mm bleed.
Front (Soft White #FAF8F3): PATIALA and JEWELERS top-left, person name in Playfair Display with a short gold line below it, then phone, website and locations in Montserrat Light, Warm Grey. A thin gold vertical divider and a WhatsApp QR code on the right.
Back (Soft Black #161513): centred monogram and lockup in gold and cream, flat and plain.
QR code: black on Soft White (never gold, never inverted), at least 20 mm wide, clear space around it, label WHATSAPP in small spaced capitals below.
Print: thick card (about 500 gsm), soft-touch black back, gold foil on the gold elements.

## Tone of voice

Warm, assured, unhurried. Short sentences and concrete details. No exclamation marks, no slang, no sales shouting, no emojis in headlines.
Examples: "Cast in 18k gold, finished by hand." "Made to be passed down." "Visit us for a private appointment."

## When designing for Patiala Jewelers

1. Use only the colours and fonts above.
2. Keep it minimal and let space do the work.
3. Check spelling of Jewelers and Patiala.
4. Make the brand the hero, then the content.
5. Output as clean HTML or SVG with real text so it can be pasted into Figma.
## Website UI rules (added October 2026, supersede anything above that conflicts for the website)

Reference: Cartier, Van Cleef & Arpels, Tiffany and Chopard (checked October 2026). Calm, white-and-black, fine hairlines, brand colour used sparingly.

Surfaces (60 / 30 / 10)
- About 70% light, 30% Soft Black, measured by section height. Gold is an accent only: the logo, the saved-heart marker and the WhatsApp icon. Never a fill, never a border.
- Soft White `#FAF8F3` is the ONLY light colour. No beige or cream backgrounds anywhere (Cream `#F3EFE6` is only text on dark surfaces). Photos load on a neutral Soft Black tint at 5%, and the map is light neutral grey.
- Sections are told apart by a fine grey line, generous space and the dark bands (the "Our story" section and the footer), not by tinted backgrounds.
- Content that must stand apart (boutiques, contact details, forms, value cards) sits in a card with a fine grey border and no fill.
- Inner pages open with a title block that ends in a fine line.

Borders
- Dividers and card edges: fine grey hairline, Soft Black at 10 to 16% opacity.
- Form fields and outline buttons: a clear 1px Soft Black border (fields at 50%), like Cartier's.
- No gold borders. No borders on the floating WhatsApp button.

Text
- Body: Montserrat Light 300, 16px, Soft Black.
- Secondary text: Soft Black at 78% (replaces Warm Grey `#6A6458`, which was too faint at Light weight).
- Small uppercase labels, nav links, buttons and form labels: Montserrat Regular 400 at 11.5 px or larger. Light is too thin at those sizes. Still never bold.

Header and motion
- The header height, logo size and wordmark follow the scroll position directly (no timed animation), so they never lag a fast scroll.
- Smooth scrolling uses Lenis and is off for people who ask for reduced motion.

### Contrast update (October 2026)
- Body text is Montserrat Regular 400 (was Light 300). Secondary text is Soft Black at 88%. Labels use .22em tracking, not .32em.
- On dark bands, secondary text is Cream at 85 to 90%.
- Fine lines are Soft Black at 15 to 22%.
- Breadcrumbs: phones show only a back link to the category, never the full path or product name.
