# Patiala Jewelers: Project Requirements

A small, calm, luxury showcase website for Patiala Jewelers (Gold & Diamonds, Islamabad). Visitors look at pieces and get in touch. They cannot buy online.

Visual rules live in `design.md`. This file says what the site contains and how it behaves.

---

## 1. Goals

1. Make the brand feel premium and trustworthy within five seconds.
2. Let people browse the pieces easily.
3. Turn browsing into a WhatsApp message, a call or a boutique visit.
4. Let the owner manage everything without a developer.

Success means more WhatsApp chats and more boutique visits.

## 2. Principles

- Quiet luxury. Few elements, lots of space, one idea per section.
- Simple to use on a phone first. Most visitors will be on mobile.
- Simple to build and maintain. Nothing that needs special tools.
- If something does not help a visitor reach the shop, leave it out.

## 3. Scope

**In**
- Five main pages (below) plus a small Favorites page
- Product browsing with filters
- Enquiry through WhatsApp or a short form
- Admin panel for the owner
- Floating WhatsApp button

**Out (not now)**
- Online buying, cart, checkout, payments
- Customer accounts and sign-up
- Search, blog, reviews, live chat, multiple languages
- Any imagery of people. Product-only photography.

## 4. Site map

```
Home
Collections ── Product page
Our Story
Contact (includes the four boutiques)
Favorites (small, opened from the heart icon)
```

Header: Home · Collections · Our Story, logo in the centre, icons for Favorites, Boutiques and Contact on the right.
Mobile: logo on the left, icons and menu button on the right.

## 5. Pages

### 5.1 Home
Keep it short. Five sections, in this order:
1. **Hero:** full-width light product photo, one heading, one line, one button ("Discover the selection"). Slideshow of 2 to 4 slides at most.
2. **Collections:** three to six category tiles (for example Rings, Necklaces, Bangles, Earrings, Bridal).
3. **Selected pieces:** four to eight featured products, picked by the owner.
4. **Our story teaser:** one photo, two short sentences, link to Our Story.
5. **Boutiques:** the four locations in one calm line with a link to Contact.

Removed to keep it clean: the Appointment / Bespoke / Care row and the extra campaign banner.

### 5.2 Collections
- Heading and a thin row of category names to switch between. Optional metal filter (Gold, Silver, Platinum, and so on).
- Grid of products: photo, name, optional price. Square photos, a lot of space between them.
- Twelve per page with simple Next and Previous.

### 5.3 Product page
The page that leads to a conversation. See section 6.
- Photo gallery: one large photo plus a few thumbnails.
- Name, category, short description.
- Details: metal, purity, weight, stone (only what applies).
- Price or "Price on request" (owner chooses per product).
- Buttons: **Enquire on WhatsApp** (main), **Send an enquiry** (form), heart to save.
- Up to four related pieces.

### 5.4 Our Story
- Heading, one photo, a short story (edited in the admin), one closing line.
- Optional: three short values (hallmarked gold, certified diamonds, finished by hand).
- A single button to Contact.

### 5.5 Contact
- The four boutiques (PWD, DHA II, Ghauri Town, F-7): address, phone, hours, "Get directions" link.
- Direct contact: phone, WhatsApp, email.
- Short form: name, phone, message. Email is optional.
- Opening a boutique shows its map location in Google Maps.

### 5.6 Favorites
- Pieces the visitor hearted, saved in their own browser (no account).
- Button: **Send my list on WhatsApp**. It opens a message listing the piece names and links.
- Empty state: one calm line and a link to Collections.

## 6. How a visitor enquires (no purchase)

1. Visitor finds a piece.
2. They tap **Enquire on WhatsApp**. WhatsApp opens with a ready message:
   *"Hello, I am interested in [Piece name]. [Link]"*
3. Or they fill the short form. It lands in the admin under Enquiries.
4. The owner replies, then invites them to a boutique.

No price negotiation, payment or delivery on the site.

## 7. Floating WhatsApp button

A quiet, premium button that matches the brand. It must never feel like a sales pop-up.

- **Shape and colour:** square, flat, Soft Black fill, a thin gold hairline border, a gold WhatsApp symbol. No green, no gradient, no shadow, no pulsing, no bounce.
- **Position:** bottom right, 20px from the edges. On phones it stays clear of the browser bar.
- **Appears:** after the visitor scrolls a little (about 300px), with a soft fade.
- **On hover (desktop):** the button slides open a little to show the words "Chat with us" in small spaced capitals, in cream.
- **On tap:** opens WhatsApp with a short ready message ("Hello, I would like to know more about your jewelry."). On product pages the message names the piece.
- **Hidden** while the mobile menu is open.
- **One number**, set in the admin. If empty, the button does not show.
- **Accessible:** proper label, keyboard focus ring in gold.

## 8. Admin panel

The owner logs in at `/admin/`. Everything below is already built unless marked.

| Section | What the owner can do |
|---|---|
| Hero slides | Upload photos, set heading, line, link, text colour, order, show or hide |
| Categories | Name, photo, order, show or hide |
| Products | Name, category, description, metal, purity, weight, stone, price (or none), main photo, extra photos, featured, show or hide |
| Enquiries | Read messages from the site, mark New, Contacted or Closed, add private notes |
| Branches | Four boutiques: address, phone, hours, map link, order |
| Store information | Name, descriptor, tagline, phone, WhatsApp number, email, Instagram and Facebook links, Our Story text and photo |

Needed next: a simple "pieces count" on the dashboard and an export of enquiries to a spreadsheet (optional).

## 9. Design

Follow `design.md` exactly. In short:
- Colours: Gold `#B8975A`, Soft Black `#161513`, Soft White `#FAF8F3` (plus the four helper colours).
- Fonts: Playfair Display Regular for headings, Montserrat Light for everything else. No bold.
- Flat fills, thin gold lines, square corners, no shadows or gradients.
- Photography: light, calm, one piece per frame, no people.
- Tone: warm, assured, short sentences. No exclamation marks.
- Always spell it "Jewelers".

Reference for feel: the Cartier website (centred logo, clean header, full-width hero). We take the layout idea, not their look.

## 10. Content needed from the client

- [ ] Logo files (already received: `logo.svg`, `logo.png`)
- [ ] Final category list
- [ ] Product photos (light, clean, one piece per photo) and details
- [ ] Prices: show them, or "Price on request"?
- [ ] Main WhatsApp number and email
- [ ] Phone, address, hours and map location for each boutique
- [ ] Our Story text (100 to 150 words) and one photo
- [ ] Instagram and Facebook links
- [ ] Domain name (`patialajewelersofficial.com`) and hosting choice

## 11. Technical

- **Stack:** Django, HTML, CSS and a little JavaScript. No React. SQLite to start.
- **Pages load fast:** images resized and compressed, lazy loading below the first screen.
- **Mobile first:** tested at 360, 390, 768, 1024 and 1440 px wide. No sideways scrolling.
- **Search engines:** proper page titles, descriptions, and sharing images for each page and product.
- **Accessibility:** readable contrast, keyboard friendly, text alternatives for images, no motion for people who turn it off.
- **Security:** admin behind a strong password, spam protection on forms, HTTPS in production.
- **Hosting:** any small Linux host or a managed Django host. Media files (product photos) are backed up.

## 12. Status

| Area | State |
|---|---|
| Project setup, database, admin | Done |
| Header (desktop and mobile), footer | Done |
| Hero with video | Done (`static/img/hero/`) |
| Home, Collections, Product, Our Story, Contact, Favorites | Front end done, using demo products with image links |
| Enquiry forms and saving to admin | Done |
| WhatsApp floating button | Done (premium version) |
| Favorites saving and WhatsApp list | Done, saved in the visitor's browser |
| Real content and photos | Waiting on client |
| Back end polish (dashboard counts, enquiry export) | Not started |

## 13. Build order

1. Home page sections (5.1) and WhatsApp button (7).
2. Collections and Product page, including the WhatsApp enquiry link.
3. Contact page with the four boutiques.
4. Our Story page.
5. Favorites (hearts and the WhatsApp list).
6. Real content, speed and search-engine pass, then launch.

## 14. Open questions

1. Show prices, or "Price on request" for everything?
2. One WhatsApp number for the whole brand, or one per boutique?
3. Is Favorites worth keeping? If not, we remove the heart and the page.
4. English only, or also Urdu later?
