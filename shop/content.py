"""Every editable line of text on the site, with its starting value.

These are only the starting values: they are copied into the database (Admin → Page text) by a migration and by
`seed_demo`, and the site always reads the database. If a row is ever missing, the starting value is used so a page never breaks.
Keys use underscores so templates can print them as {{ txt.home_hero_text }}.
"""

# key: (group, what it is, starting text)
DEFAULTS = {
    # ---- Home
    "home_hero_text": ("Home", "Hero: line under the title", "Hallmarked gold and certified diamonds, finished by hand in Islamabad."),
    "home_hero_button": ("Home", "Hero: button", "Discover the collections"),
    "home_services_button": ("Home", "Services: link", "All services"),
    # ---- Collections
    "collections_label": ("Collections", "Page: small label", "Collections"),
    "collections_title": ("Collections", "Page: heading when all pieces show", "All pieces"),
    "collections_empty": ("Collections", "Message when no piece matches", "No pieces match your selection."),
    "product_related_title": ("Collections", "Product page: heading above related pieces", "You may also like"),
    "product_note": ("Collections", "Product page: note under the buttons", "Visit any boutique to see this piece in person."),
    "product_enquiry_label": ("Collections", "Product page: enquiry small label", "Prefer a call back"),
    "product_enquiry_title": ("Collections", "Product page: enquiry heading", "Send an enquiry"),
    # ---- Services
    "services_label": ("Services", "Page: small label", "Services"),
    "services_title": ("Services", "Page: heading", "Care for every piece"),
    "services_lead": ("Services", "Page: line under the heading", "Bring your jewelry to any boutique and our craftsmen will look after it."),
    "service_text_label": ("Services", "Service page: small label above the description", "The service"),
    "service_included_label": ("Services", "Service page: label above the list", "What is included"),
    "service_steps_label": ("Services", "Service page: steps small label", "How it works"),
    "service_steps_title": ("Services", "Service page: steps heading", "Three simple steps"),
    "service_facts_where": ("Services", "Service page: the Where value", "Any boutique"),
    "service_cta_title": ("Services", "Service page: closing line", "Ready when you are."),
    "service_cta_link": ("Services", "Service page: link under the button", "Or send a message"),
    "service_more_label": ("Services", "Service page: other services small label", "More services"),
    "service_more_title": ("Services", "Service page: other services heading", "Also at our boutiques"),
    # ---- About
    "about_label": ("About", "Page: small label", "About"),
    "about_button": ("About", "Link under the story text", "Visit a boutique"),
    "about_quote": ("About", "Closing line", "Made to be passed down."),
    "about_quote_button": ("About", "Closing button", "Discover the collections"),
    # ---- Contact
    "contact_label": ("Contact", "Page: small label", "Contact"),
    "contact_title": ("Contact", "Page: heading", "Visit us for a private appointment"),
    "contact_direct_title": ("Contact", "Heading above the contact details", "Speak with us"),
    "contact_form_title": ("Contact", "Heading above the form", "Send a message"),
    # ---- Favorites
    "favorites_label": ("Favorites", "Page: small label", "Favorites"),
    "favorites_title": ("Favorites", "Page: heading", "Your favorites"),
    "favorites_lead": ("Favorites", "Page: line under the heading", "Pieces you save with the heart are kept in this browser."),
    "favorites_empty": ("Favorites", "Message when nothing is saved", "You have not saved any pieces yet."),
    "contact_thanks": ("Contact", "Message after a form is sent", "Thank you. We will be in touch shortly."),
    # ---- Everywhere
    "whatsapp_message": ("Everywhere", "First message in the WhatsApp button", "Hello, I would like to know more about your jewelry."),
    "whatsapp_label": ("Everywhere", "WhatsApp button text", "Chat with us"),
}

# title, text
ABOUT_VALUES = [
    ("Hallmarked gold", "Every piece is tested and stamped for purity."),
    ("Certified diamonds", "Each stone is graded before it is set."),
    ("Finished by hand", "Polished and checked twice by our craftsmen."),
]
