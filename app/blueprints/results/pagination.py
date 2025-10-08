from flask_paginate import Pagination
from markupsafe import Markup

SVG_RIGHT = (
    '<svg width="24" height="24" viewBox="0 0 24 24" fill="none">'
    '<path d="M8 6.47597L9.47597 5L16.476 12L9.47597 19L8 17.524L13.5232 12L8 6.47597Z" fill="#007BC7"/></svg>'
)
SVG_LEFT = (
    '<svg width="24" height="24" viewBox="0 0 24 24" fill="none">'
    '<path d="M16 6.47597L14.52403 5L7.524 12L14.52403 19L16 17.524L10.4768 12Z" fill="#007BC7"/></svg>'
)


def _adapt_previous_page(prev_page: str) -> str:
    return prev_page.replace('<span aria-hidden="true">&laquo;</span><span class="sr-only">Previous</span>', SVG_LEFT)


def _adapt_next_page(next_page: str) -> str:
    return next_page.replace('<span aria-hidden="true">&raquo;</span><span class="sr-only">Next</span>', SVG_RIGHT)


def create_navigation(pagination: Pagination) -> Markup:
    """
    Create a Markup object for the pagination navigation links by adapting pages that are present
    in the `pagination` object.
    """
    s = ['<nav aria-label="..."><ul class="pagination">']  # begin the navigation object

    # add and adapt the 'previous' button if needed
    s.append(_adapt_previous_page(pagination.prev_page)) if pagination.has_prev else None
    for page in pagination.pages:
        if page:
            single_page = pagination.single_page(page)
            if "page-item active" in single_page:  # adapt the 'current' page
                single_page = f'<li class="page-item active"><a class="page-link">{page}</a></li>'
            s.append(single_page)
        else:  # insert filler page
            s.append(pagination.gap_marker_fmt)

    # add and adapt the 'next' button if needed
    s.append(_adapt_next_page(pagination.next_page)) if pagination.has_next else None
    s.append('</ul></nav>')  # end the navigation object

    return Markup("".join(s))  # noqa S704
