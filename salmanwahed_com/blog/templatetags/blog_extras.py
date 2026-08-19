from math import ceil

import markdown
from bs4 import BeautifulSoup
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

from blog.models import BlogPost

register = template.Library()

MARKDOWN_EXTENSIONS = [
    "fenced_code",  # ``` blocks
    "codehilite",  # Pygments classes, styled by assets/css/code.css
    "tables",
    "toc",  # ids on headings so they can be linked to
    "sane_lists",
    "attr_list",
]

MARKDOWN_CONFIG = {
    # guess_lang off: an unlabelled fence stays plain rather than being
    # highlighted as whatever Pygments guesses, which is wrong more often
    # than it is right.
    "codehilite": {"css_class": "codehilite", "guess_lang": False},
}


def _rendered_body(post):
    """Post body as HTML, rendered once per object.

    Legacy CKEditor posts are stored as HTML and pass straight through; anything
    newer is Markdown. The result is memoised on the instance because a single
    page render asks for it twice -- once for the body, once to count words for
    the reading time.
    """
    cached = getattr(post, "_rendered_body_cache", None)
    if cached is not None:
        return cached

    if post.body_format == BlogPost.BodyFormat.MARKDOWN:
        html = markdown.markdown(
            post.body,
            extensions=MARKDOWN_EXTENSIONS,
            extension_configs=MARKDOWN_CONFIG,
        )
    else:
        html = post.body

    post._rendered_body_cache = html
    return html


@register.simple_tag
def render_body(post):
    """Render a post body, honouring its body_format."""
    return mark_safe(_rendered_body(post))


@register.simple_tag
def minutes_to_read(post):
    """Reading time from the rendered body, so Markdown syntax is not counted."""
    soup = BeautifulSoup(_rendered_body(post), features="html.parser")
    words = soup.text.split()
    minutes_read = ceil(len(words) / settings.WPM_READ)
    if minutes_read > 1:
        return f"{minutes_read} minutes read"
    else:
        return f"{minutes_read} minute read"
