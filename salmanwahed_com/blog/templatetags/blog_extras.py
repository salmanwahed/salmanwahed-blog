from math import ceil
from django import template
from bs4 import BeautifulSoup

register = template.Library()


@register.simple_tag
def minutes_to_read(body):
    soup = BeautifulSoup(body, features="html.parser")
    words = soup.text.split()
    minutes_read = ceil(len(words)/150)
    if minutes_read > 1:
        return f"{minutes_read} minutes read"
    else:
        return f"{minutes_read} minute read"