from flask_babel import lazy_gettext

ENDANGERMENT_MAPPING = {
    "A": lazy_gettext(
        "/static/fact_sheets_nl/Vakbijlage Gevaarzetting Super Cobra 6 en vergelijkbare artikelen v2-22032024.pdf"
    ),
    "B": lazy_gettext(
        "/static/fact_sheets_nl/Vakbijlage Gevaarzetting Cobra 8 en vergelijkbare artikelen v2-05112024 .pdf"
    ),
    "C": lazy_gettext("/static/fact_sheets_nl/Vakbijlage Gevaarzetting signaalraketten v1-23042024.pdf"),
    "D": lazy_gettext("/static/fact_sheets_nl/Vakbijlage Gevaarzetting shells v1-22032024.pdf"),
    "F": lazy_gettext("/static/fact_sheets_nl/Vakbijlage Gevaarzetting nitraten v1-02042024.pdf"),
}
