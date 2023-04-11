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


def parse_book_page(response):
    soup = BeautifulSoup(response.text, "lxml")
    title_tag = soup.find("h1")
    image_tag = soup.find("div", class_="bookimage").find("img")["src"]
    comments_tag_list = soup.find_all("div", class_="texts")
    genre_tags = soup.find("span", class_="d_book").find_all("a")

    genres_list = [genre_tag.text for genre_tag in genre_tags]

    comments_list = [comment_tag.find("span").text for comment_tag in comments_tag_list]

    image_extension = os.path.splitext(image_tag)[1]
    image_url = urljoin(TULULU_BASE_URL, image_tag)

    title_text = title_tag.text
    splitted_title = title_text.strip().split("::")

    title = splitted_title[0].strip()
    author = splitted_title[1].strip()

    book_params = {
        "title": title,
        "author": author,
        "image_url": image_url,
        "image_extension": image_extension,
        "comments_list": comments_list,
        "genres_list": genres_list
    }

    return book_params


if __name__ == "__main__":
    for book_id in range(1, 10):
        book_url = urljoin(TULULU_BASE_URL, f'b{book_id}')

        response = requests.get(book_url)
        response.raise_for_status()
        try:
            check_for_redirect(response)
            book_params = parse_book_page(response)
            download_txt(book_id, f"{book_id}. {book_params['title']}")
            download_image(book_params["image_url"], f"{book_id}{book_params['image_extension']}")
        except ErrRedirection:
            logging.warning("Было перенаправление")
