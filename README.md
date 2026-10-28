# Patiala Jewelers

Website for Patiala Jewelers (Gold & Diamonds, Islamabad), built with Django and plain HTML, CSS and JS templates. All design rules come from `design.md`.

## Pages
| URL | Page |
|---|---|
| `/` | Home: hero, categories, featured pieces |
| `/collections/` | All products, filterable by category, metal and search |
| `/collections/<slug>/` | Product detail with photo gallery and enquiry form |
| `/about/` | Brand story (editable in admin) |
| `/contact/` | Store details, map and contact form |
| `/admin/` | Admin panel |

## Admin panel
- **Categories**: name, image, display order, show/hide
- **Products**: details, price (blank shows "Price on request"), main photo plus gallery, featured and visible toggles
- **Enquiries**: messages from the contact and product forms, with status and internal notes
- **Branches**: the store locations (PWD, DHA II, Ghauri Town, F-7) with address, phone, hours and map
- **Store information**: name, descriptor, tagline, phone, WhatsApp, email, socials, About page text

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
