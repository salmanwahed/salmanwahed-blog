from math import ceil
from django import template
from bs4 import BeautifulSoup

register = template.Library()


@register.simple_tag
def minutes_to_read(body):
    soup = BeautifulSoup(body, features="html.parser")
    words = soup.text.split()
    return ceil(len(words)/150)