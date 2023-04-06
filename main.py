import logging
import requests
import os
from bs4 import BeautifulSoup
import lxml
from pathvalidate import sanitize_filename
from urllib.parse import urljoin


TULULU_BASE_URL = "https://tululu.org/"


class ErrRedirection(Exception):
    pass


def check_for_redirect(response):
    if response.url == "https://tululu.org/":
        raise ErrRedirection


def download_txt(book_id, filename, folder='books/'):
    txt_url = urljoin(TULULU_BASE_URL, "txt.php")
    payload = {
        "id":book_id
    }

    response = requests.get(txt_url, params=payload)
    response.raise_for_status()

    book_path = f"{urljoin(folder, sanitize_filename(filename))}.txt"
    os.makedirs(folder, exist_ok=True)

    check_for_redirect(response)
    with open(book_path, "wb") as file:
        file.write(response.content)

    return book_path


def download_image(image_url, filename, folder='images/'):
    response = requests.get(image_url)
    response.raise_for_status()

    image_path = f"{urljoin(folder, sanitize_filename(filename))}"
    os.makedirs(folder, exist_ok=True)

    check_for_redirect(response)
    with open(image_path, "wb") as image:
        image.write(response.content)

    return image_path


def webpage_parsing(response):
    soup = BeautifulSoup(response.text, "lxml")
    title_tag = soup.find("h1")
    image_tag = soup.find("div", class_="bookimage").find("img")["src"]

    image_extension = os.path.splitext(image_tag)
    image_url = urljoin(TULULU_BASE_URL, image_tag)
    title_text = title_tag.text
    splitted_title = title_text.strip().split("::")

    title = splitted_title[0].strip()
    author = splitted_title[1].strip()

    return title, author, image_url, image_extension[1]


if __name__ == "__main__":
    for book_id in range(1, 10):
        book_url = urljoin(TULULU_BASE_URL, f'b{book_id}')

        response = requests.get(book_url)
        response.raise_for_status()
        try:
            check_for_redirect(response)
            title, author, image_url, image_extension = webpage_parsing(response)
            download_txt(book_id, f"{book_id}. {title}")
            download_image(image_url, f"{book_id}{image_extension}")
        except ErrRedirection:
            logging.warning("Было перенаправление")
