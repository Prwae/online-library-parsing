import os
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

TULULU_BASE_URL = "https://tululu.org/"


class ErrRedirection(Exception):
    pass


def check_for_redirect(response):
    if response.url == "https://tululu.org/":
        raise ErrRedirection


def download_txt(book_id, filename, folder="books/"):
    txt_url = urljoin(TULULU_BASE_URL, "txt.php")
    payload = {
        "id": book_id
    }

    response = requests.get(txt_url, params=payload)
    response.raise_for_status()

    book_path = f"{urljoin(folder, sanitize_filename(filename))}.txt"
    os.makedirs(folder, exist_ok=True)

    with open(book_path, "wb") as file:
        file.write(response.content)

    return book_path


def download_image(image_url, filename, folder="images/"):
    response = requests.get(image_url)
    response.raise_for_status()

    image_path = f"{urljoin(folder, sanitize_filename(filename))}"
    os.makedirs(folder, exist_ok=True)

    with open(image_path, "wb") as image:
        image.write(response.content)

    return image_path


def parse_book_page(response):
    soup = BeautifulSoup(response.text, "lxml")

    title_tag_selector = "h1"
    image_tag_selector = "div.bookimage img"
    comments_tags_selector = "div.texts"
    genre_tags_selector = "span.d_book a"
    comment_text_selector = "span.black"

    title_tag = soup.select_one(title_tag_selector)
    image_tag = soup.select_one(image_tag_selector)["src"]
    comments_tags = soup.select(comments_tags_selector)
    genre_tags = soup.select(genre_tags_selector)

    genres = [genre_tag.text for genre_tag in genre_tags]

    comments = [comment_tag.select(comment_text_selector)[0].text for comment_tag in comments_tags]

    image_extension = os.path.splitext(image_tag)[1]
    image_url = urljoin(response.url, image_tag)

    title_text = title_tag.text
    title, author = title_text.strip().split("::")

    book_params = {
        "title": title.strip(),
        "author": author.strip(),
        "image_url": image_url,
        "image_extension": image_extension,
        "comments": comments,
        "genres": genres
    }

    return book_params
