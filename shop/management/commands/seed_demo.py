"""
Fill the site with demo content so the front end looks complete.

Photos are hotlinked from Unsplash (free licence, product-only shots) through the
"image link" fields, so nothing is downloaded. Replace them from the admin later.

    python manage.py seed_demo           # add or refresh demo content
    python manage.py seed_demo --clear   # remove demo products and categories first
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from shop.models import Branch, Category, Product, ProductImage, Service, StoreInfo

PHOTO = "https://images.unsplash.com/photo-{}?w=1000&q=75&auto=format&fit=crop"

CATEGORIES = [
    ("Rings", "Solitaires, halos and bands, set by hand.", "1603561591411-07134e71a2a9"),
    ("Necklaces", "Fine chains and pendants for every day.", "1786052337650-9e1c0dd01f5e"),
    ("Earrings", "Studs, hoops and jhumkas in gold and diamonds.", "1589095053205-8fc842336f4a"),
    ("Bangles", "Cast in gold, finished with a hand polish.", "1611591437281-460bfbe1220a"),
    ("Bridal", "Complete sets for the day that matters.", "1721807644561-9efcabee5c42"),
]

# category, name, metal, purity, weight, stone, price, photo, featured, description
PRODUCTS = [
    ("Rings", "Emerald-Cut Solitaire Ring", "gold", "18K", "3.800", "Diamond", 285000, "1598560917807-1bae44bd2be8", True,
     "A single emerald-cut diamond on a slim pavé band. Cast in 18k yellow gold and finished by hand."),
    ("Rings", "Pink Sapphire Halo Ring", "rose_gold", "18K", "4.200", "Pink sapphire, diamond", 340000, "1603561591411-07134e71a2a9", True,
     "A cushion-cut pink sapphire framed by a halo of small diamonds, in warm rose gold."),
    ("Rings", "Pear Diamond Halo Ring", "white_gold", "18K", "3.500", "Diamond", 410000, "1605100804567-1ffe942b5cd6", False,
     "A pear-cut centre stone with a delicate halo and a milgrain band."),
    ("Rings", "Round Brilliant Solitaire", "platinum", "950", "4.600", "Diamond", 620000, "1768423685978-42fe24ec39a0", True,
     "A six-prong round brilliant in platinum. Simple, timeless, made to last."),
    ("Rings", "Classic Wedding Bands", "gold", "22K", "9.400", "", 265000, "1766963026693-e73b058176dd", False,
     "A matching pair of plain bands in 22k gold, comfort-fit and polished."),
    ("Rings", "Trio Stacking Rings", "white_gold", "18K", "5.100", "Diamond", 195000, "1719924998065-0c60e329ef58", False,
     "Three slim rings, each set with a single diamond. Wear them together or apart."),

    ("Necklaces", "Diamond Halo Pendant", "white_gold", "18K", "3.100", "Diamond", 175000, "1589128777073-263566ae5e4d", True,
     "A cushion halo pendant on a fine box chain."),
    ("Necklaces", "Pearl Drop Pendant", "gold", "18K", "2.400", "Pearl", 98000, "1786052337650-9e1c0dd01f5e", False,
     "A single pearl held in a soft gold teardrop."),
    ("Necklaces", "Circle Chain Necklace", "gold", "18K", "4.000", "", 120000, "1773929345739-94db8a4ccd0c", True,
     "A hand-formed gold circle on a double cable chain."),
    ("Necklaces", "Bar Pendant Chain", "rose_gold", "18K", "3.300", "Diamond", 135000, "1771515411694-57fb626159d1", False,
     "A slim bar set with small diamonds, hung on a rose gold chain."),
    ("Necklaces", "Fine Gold Chain Set", "gold", "22K", "11.200", "", 310000, "1611107683227-e9060eccd846", False,
     "A light chain with matching bangles and a small ring. Cast in 22k gold."),
    ("Necklaces", "Layered Pendant Necklace", "gold", "18K", "5.800", "", 148000, "1569397288884-4d43d6738fbd", False,
     "A long chain with a flat bar pendant, made for layering."),

    ("Earrings", "Gold Jhumka Earrings", "gold", "22K", "14.500", "", 365000, "1589095053205-8fc842336f4a", True,
     "Dome jhumkas with fine filigree, cast in 22k gold."),
    ("Earrings", "Ruby Cluster Earrings", "gold", "18K", "4.700", "Ruby, diamond", 158000, "1588891805983-fee12d508e31", False,
     "An oval ruby ringed with small diamonds."),
    ("Earrings", "Diamond Leaf Studs", "white_gold", "18K", "3.900", "Diamond", 225000, "1693213085235-ea6deadf8cee", True,
     "Leaf-shaped studs set with round diamonds."),
    ("Earrings", "Tri-Tone Hoops", "gold", "18K", "6.200", "", 112000, "1615655114865-4cc1bda5901e", False,
     "Three bands in yellow, white and rose gold, joined as one hoop."),
    ("Earrings", "Rose Gold Dome Drops", "rose_gold", "18K", "3.600", "", 88000, "1701777892740-88419a701472", False,
     "A small domed drop with a fine pierced pattern."),
    ("Earrings", "Diamond Drop Earrings", "white_gold", "18K", "5.400", "Diamond", 295000, "1665159882377-385d68d2bdff", False,
     "Long drops set with graduated diamonds."),

    ("Bangles", "Rose Gold Pavé Bangle", "rose_gold", "18K", "12.600", "Diamond", 275000, "1611591437281-460bfbe1220a", True,
     "A slim bangle set all around with small diamonds."),
    ("Bangles", "Gold Bamboo Bangles", "gold", "22K", "28.000", "", 495000, "1690175867343-2af70ea57537", False,
     "A pair of bamboo-textured bangles with diamond-set joints."),
    ("Bangles", "Ruby Kada Set", "gold", "22K", "36.000", "Ruby", 640000, "1617191880362-aac615de3c26", True,
     "Two kadas set with rubies in a hand-carved gold frame."),
    ("Bangles", "Diamond Tennis Bracelet", "white_gold", "18K", "9.800", "Diamond", 540000, "1573408301185-9146fe634ad0", False,
     "A continuous line of diamonds in white gold."),
    ("Bangles", "Slim Diamond Bangle", "gold", "18K", "6.400", "Diamond", 185000, "1655707063513-a08dad26440e", False,
     "A thin bangle with a row of small diamonds."),
    ("Bangles", "Engraved Gold Bangles", "gold", "22K", "32.000", "", 560000, "1679156271456-d6068c543ee7", False,
     "A set of engraved bangles with a classic pattern."),

    ("Bridal", "Bridal Choker Set", "gold", "22K", "62.000", "Ruby, pearl", 1150000, "1721807644561-9efcabee5c42", True,
     "A choker, long necklace, earrings and maang tikka, cast in 22k gold."),
    ("Bridal", "Ruby Bridal Necklace Set", "gold", "22K", "54.000", "Ruby, diamond", 1380000, "1727947074642-0bd47ef70b58", False,
     "A layered necklace with a pendant and matching earrings."),
    ("Bridal", "Bridal Jhumka Pair", "gold", "22K", "21.000", "Pearl", None, "1651160670627-2896ddf7822f", False,
     "Large jhumkas with pearl drops. Made to order."),
]

# name, area, latitude, longitude (from OpenStreetMap). These mark the area, not the exact shop:
# set each shop's exact pin in the admin.
BRANCHES = [
    ("PWD", "PWD Housing Society", "33.571279", "73.144798"),
    ("DHA II", "DHA Phase II", "33.527273", "73.160908"),
    ("Ghauri Town", "Ghauri Town", "33.619176", "73.142770"),
    ("F-7", "Jinnah Super Market, F-7", "33.720470", "73.056311"),
]


# name, summary, intro, description, includes, process, turnaround, price, photo
SERVICES = [
    ("Polishing", "Restores the shine of gold and diamond pieces.", "Bring back the shine.",
     "A careful hand polish removes fine scratches and brings back the original brilliance of your piece.",
     "Hand polish to remove fine scratches\nSetting and prong check\nUltrasonic clean\nFinal inspection under light",
     "Bring it in|Visit any boutique and we look at your piece with you.\nPolished by hand|Our craftsmen polish and clean it in the workshop.\nCollect it|We call you when it is ready, often the same day.",
     "Same day", "Complimentary", "1758995116383-f51775896add"),
    ("Repair", "Broken clasps, chains and settings made good again.", "Made good again.",
     "From a snapped chain to a loose stone, we repair the piece by hand and test it before it leaves the workshop.",
     "Chain and clasp repair\nStone re-setting\nProng re-tipping\nSoldering and finishing",
     "Show us the damage|We assess the piece and agree the repair with you.\nRepaired by hand|The work is done in our own workshop.\nTested and returned|We check it twice before you collect it.",
     "3 to 5 days", "From Rs 1,500", "1611107683227-e9060eccd846"),
    ("Resizing", "Rings and bangles fitted to your measure.", "Fitted to your measure.",
     "We resize rings and bangles in gold and platinum, keeping the design and any engraving intact.",
     "Accurate sizing\nRing and bangle resizing\nEngraving kept intact\nFinal polish",
     "Get measured|We measure your finger or wrist in the boutique.\nResized by hand|The piece is adjusted and refinished.\nTry it on|You check the fit when you collect it.",
     "2 to 3 days", "From Rs 2,000", "1768423685978-42fe24ec39a0"),
    ("Cleaning", "A deep clean for diamonds and gemstones.", "Clear, bright stones.",
     "Ultrasonic cleaning lifts away the oils and dust that dull a stone. Safe for diamonds and most gemstones.",
     "Ultrasonic cleaning\nSteam clean\nStone and setting check\nSoft-cloth finish",
     "Hand it over|Leave your piece with us or wait in the boutique.\nDeep cleaned|We clean it and check every stone.\nReturned bright|It is handed back ready to wear.",
     "While you wait", "Complimentary", "1589128777073-263566ae5e4d"),
    ("Custom design", "A piece made to your own design.", "Made for you alone.",
     "Bring an idea or a sketch. We draw it, agree the details with you and craft it in the metal and stones you choose.",
     "Design consultation\nSketch and approval\nMetal and stone selection\nHand finishing",
     "Share your idea|Tell us what you have in mind.\nWe draw it|You approve the design before we begin.\nCrafted by hand|We make it and call you when it is ready.",
     "3 to 4 weeks", "On request", "1603561591411-07134e71a2a9"),
    ("Valuation", "A written valuation for insurance or resale.", "Know what it is worth.",
     "A certified appraisal of your gold and stones, with a written report you can keep for insurance or resale.",
     "Gold purity testing\nStone grading\nWritten valuation report\nInsurance-ready copy",
     "Bring your piece|Visit any boutique with your jewelry.\nAppraised|Our team tests and grades it.\nReceive your report|You collect a signed written valuation.",
     "1 to 2 days", "From Rs 3,000", "1605100804567-1ffe942b5cd6"),
]


class Command(BaseCommand):
    help = "Add demo categories, products and store details."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Delete all products and categories first.")

    def handle(self, *args, **opts):
        if opts["clear"]:
            Product.objects.all().delete()
            Category.objects.all().delete()

        cats = {}
        for i, (name, desc, photo) in enumerate(CATEGORIES):
            cat, _ = Category.objects.update_or_create(
                name=name,
                defaults={"description": desc, "image_url": PHOTO.format(photo), "display_order": i, "is_active": True},
            )
            cats[name] = cat

        by_cat = {}
        # Newest first on the site, so create them in reverse to keep the list order above.
        for cat, name, metal, purity, weight, stone, price, photo, featured, desc in reversed(PRODUCTS):
            product, _ = Product.objects.update_or_create(
                name=name,
                defaults={
                    "category": cats[cat], "description": desc, "metal": metal, "purity": purity,
                    "weight_grams": Decimal(weight), "gemstone": stone,
                    "price": Decimal(price) if price else None,
                    "image_url": PHOTO.format(photo), "is_featured": featured, "is_active": True,
                },
            )
            by_cat.setdefault(cat, []).append((product, photo))

        # Gallery: two more photos from the same category, so the thumbnails have something to show.
        for cat, items in by_cat.items():
            for n, (product, _) in enumerate(items):
                product.gallery.all().delete()
                for k in (1, 2):
                    other = items[(n + k) % len(items)]
                    if other[0] is not product:
                        ProductImage.objects.create(
                            product=product, image_url=PHOTO.format(other[1]),
                            alt_text=product.name, display_order=k,
                        )

        info = StoreInfo.load()
        info.name = "Patiala Jewelers"
        info.descriptor = "Gold & Diamonds"
        info.tagline = "Endless Luxury"
        info.phone = info.phone or "+92 51 000 0000"
        info.whatsapp = info.whatsapp or "923001234567"
        info.email = info.email or "hello@patialajewelersofficial.com"
        info.about_heading = "Our Story"
        if not info.about_text:
            info.about_text = (
                "Patiala Jewelers designs gold and diamond jewelry in Islamabad.\n\n"
                "Every piece is cast in hallmarked gold, set by hand and checked twice before it leaves the workshop. "
                "We keep our collections small, so each design gets the time it deserves.\n\n"
                "Visit any of our four boutiques and we will show you the pieces in person."
            )
        info.save()

        for i, (name, area, lat, lng) in enumerate(BRANCHES):
            Branch.objects.update_or_create(
                name=name,
                defaults={
                    "city": "Islamabad", "address": f"{area}, Islamabad",
                    "phone": "+92 51 000 0000", "opening_hours": "Mon to Sat, 11:00 AM to 8:00 PM",
                    "latitude": Decimal(lat), "longitude": Decimal(lng),
                    "display_order": i, "is_active": True,
                },
            )

        for i, (name, summary, intro, desc, inc, proc, turn, price, photo) in enumerate(SERVICES):
            Service.objects.update_or_create(
                name=name,
                defaults={"summary": summary, "intro": intro, "description": desc, "includes": inc, "process": proc,
                          "image_url": PHOTO.format(photo).replace("w=1000", "w=1800"),
                          "turnaround": turn, "price_note": price, "display_order": i, "is_active": True},
            )

        self.stdout.write(self.style.SUCCESS(
            f"Demo content ready: {Category.objects.count()} categories, {Product.objects.count()} products, "
            f"{Branch.objects.count()} branches. Phone, WhatsApp and email are placeholders."
        ))
