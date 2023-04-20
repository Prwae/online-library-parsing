import logging
import os
from urllib.parse import urljoin
import argparse

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
import lxml


TULULU_BASE_URL = "https://tululu.org/"


class ErrRedirection(Exception):
    pass


def check_for_redirect(response):
    if response.url == "https://tululu.org/":
        raise ErrRedirection


def download_txt(book_id, filename, folder='books/'):
    txt_url = urljoin(TULULU_BASE_URL, "txt.php")
    payload = {
        "id": book_id
    }

    response = requests.get(txt_url, params=payload)
    response.raise_for_status()

    book_path = f"{urljoin(folder, sanitize_filename(filename))}.txt"
    os.makedirs(folder, exist_ok=True)

    check_for_redirect(response)
    with open(book_path, "wb") as file:
        file.write(response.content)

    return book_path


def download_image(image_url, filename, folder="images/"):
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
    comments_tags = soup.find_all("div", class_="texts")
    genre_tags = soup.find("span", class_="d_book").find_all("a")

    genres = [genre_tag.text for genre_tag in genre_tags]

    comments = [comment_tag.find("span").text for comment_tag in comments_tags]

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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_id", help="С какого id книги начать парсинг библиотеки", type=int, default=1)
    parser.add_argument("--end_id", help="На каком id книги закончить парсинг библиотеки", type=int, default=10)
    args = parser.parse_args()
    start_id = args.start_id
    end_id = args.end_id

    for book_id in range(start_id, end_id):
        book_url = urljoin(TULULU_BASE_URL, f'b{book_id}')

        response = requests.get(book_url)
        response.raise_for_status()
        try:
            check_for_redirect(response)
            book_params = parse_book_page(response)

            print(f"Название: {book_params['title']} \nАвтор: {book_params['author']}\n")

            download_txt(book_id, f"{book_id}. {book_params['title']}")
            download_image(book_params["image_url"], f"{book_id}{book_params['image_extension']}")
        except ErrRedirection:
            logging.warning("Было перенаправление")

