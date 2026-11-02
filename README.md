# Patiala Jewelers

Website for Patiala Jewelers (Gold & Diamonds, Islamabad), built with Django and plain HTML, CSS and JS templates. All design rules come from `design.md`.

## Pages
| URL | Page |
|---|---|
| `/` | Home: hero film, categories, featured pieces, services, story, boutiques |
| `/collections/` | All products, filterable by category, metal and search |
| `/collections/<slug>/` | Product detail with photo gallery and enquiry form |
| `/services/` | Services, each with its own page at `/services/<slug>/` |
| `/favorites/` | Pieces saved with the heart (kept in the visitor's browser) |
| `/about/` | Brand story (editable in admin) |
| `/contact/` | Store details, map and contact form |
| `/admin/` | Admin panel |

## Admin panel
Open `/admin/` and sign in. Create your login first with `python manage.py createsuperuser`. The admin lives in its own app, `panel/` (layout, dashboard, all model admins, and the visitor and click tracking in `panel/tracking.py`); `shop/` holds only the public site. Visits from localhost are counted too, so you can test it.
- **Hero**: a visual editor (add, drag to order, live computer and phone preview, one Save button)
- **Home page**: the sections below the hero as one list. Drag to reorder, switch each on or off, and add as many as you like: products (from a Collections link or the featured pieces), categories, services, image and text (photo beside or behind the words), locations, contact. Cards per row (computer and phone) and light or dark are set per section
- **Products**: a grid to browse, search and filter, quick show and feature switches, and a simple editor (details, price, main photo, more photos, live preview)
- **Categories** and **Services**: lists you reorder by dragging, with show or hide switches and a small editor
- **Locations**: your boutiques, with a click-to-place map pin. One location shows one big map
- **Enquiries**: messages from the contact and product forms, with status and internal notes
- **Page text** and **About promises**: the copy on the pages and the short promises on the About page
- **Store settings**: name, tagline, contact, socials, colours, fonts, logo, About text
- **Visitors** and **Clicks**: the tracking logs

## Demo content
The site ships with demo products so the front end looks complete. Photos are image links (Unsplash, product-only), not downloads.

```bash
python manage.py seed_demo           # add or refresh 27 demo products, 5 categories, 4 boutiques
python manage.py seed_demo --clear   # wipe products and categories first
```
Phone, WhatsApp and email in the demo are placeholders. The boutique map pins use approximate area-level coordinates: set each shop's exact latitude and longitude in Admin > Branches.

The Contact page map is MapLibre with the site's own colour style (`static/map/style.json`) on free OpenFreeMap tiles. No account or API key is needed. Set the real ones in Admin > Store information.
To use a real photo, upload it on the product; an uploaded file always wins over the image link.

The home page hero is the film in `static/img/hero/`: `hero.webm` and `hero.mp4` for desktop, and a portrait cut for phones (`hero-mobile.webm`, `hero-mobile.mp4`), with a poster for each. To replace the video, cut a wide and a tall version, like these.

## Running locally
The project lives on an exFAT drive, which doesn't support the symlinks a virtualenv needs, so the venv is kept in your home folder:

```bash
python3 -m venv ~/.venvs/patiala-jewellers     # one time
source ~/.venvs/patiala-jewellers/bin/activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser               # one time, creates the admin login
python manage.py runserver
```

Then open http://127.0.0.1:8000 (site) and http://127.0.0.1:8000/admin (admin).

Run the tests with `python manage.py test shop`.

## Production settings (environment variables)
| Variable | Example |
|---|---|
| `DJANGO_SECRET_KEY` | a long random string |
| `DJANGO_DEBUG` | `false` |
| `DJANGO_ALLOWED_HOSTS` | `patialajewelersofficial.com,www.patialajewelersofficial.com` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://patialajewelersofficial.com` |

Run `python manage.py collectstatic` on deploy. Uploaded images go in `media/`, which your web server (or a storage service) needs to serve when `DEBUG` is off.

## Brand settings (Admin → Store information)
Colours, fonts, logo and social links live in the database, in the single Store information record, and the whole site reads them:
- **Colours:** light, dark, gold, gold on dark, gold for small text, text on dark. Lines and tints follow the light and dark colours.
- **Fonts:** a primary sans (headings, names, labels), a secondary serif (paragraphs) and the logo wordmark face, all from a short list of Google Fonts, plus the heading weight.
- **Logo:** an optional monogram and favicon upload. Without one, the built-in gold monogram is used.
- **Social media:** Instagram, Facebook, TikTok, YouTube, Pinterest and X. Filled-in links appear in the footer and on the Contact page.
The map colours (`static/map/style.json`) are separate and are not driven by these settings.
