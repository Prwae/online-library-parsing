import argparse
import logging
import os
import time
from urllib.parse import urljoin
import json

import requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename


TULULU_BASE_URL = "https://tululu.org/"


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


def parse_book_paths(response):
    soup = BeautifulSoup(response.text, "lxml")
    book_tags = soup.find_all("table", class_="d_book")
    book_paths = [book_tag.find("a")["href"] for book_tag in book_tags]
    return book_paths


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


if __name__ == "__main__":
    books_params = []

    for page_num in range(1, 2):
        response = requests.get(urljoin("https://tululu.org/l55/", str(page_num)))
        response.raise_for_status()

        for book_path in parse_book_paths(response):
            book_url = urljoin(TULULU_BASE_URL, f'{book_path}')
            book_id = "".join(c for c in book_path if c.isdigit())
            try:
                response = requests.get(book_url)
                response.raise_for_status()
                book_params = parse_book_page(response)

                title = book_params["title"]
                author = book_params["author"]
                image_url = book_params["image_url"]
                image_extencion = book_params["image_extension"]
                comments = book_params["comments"]
                genres = book_params["genres"]

                print(f"Название: {title} \nАвтор: {author}\n")

                book_path = download_txt(book_id, f"{book_id}. {title}")
                image_path = download_image(image_url, f"{book_id}{image_extencion}")

                books_params.append(
                    {
                        "title": title,
                        "author": author,
                        "img_src": image_path,
                        "book_src": book_path,
                        "comments": comments,
                        "genres": genres
                    })
            except requests.exceptions.HTTPError:
                logging.warning("Произошла ошибка при обработке страницы")
            except requests.exceptions.ConnectionError:
                logging.warning("Произошла ошибка соединения")
                time.sleep(10)
    books_params_json = json.dumps(books_params, ensure_ascii=False)
    with open("books_params.json", "w", encoding="utf-8") as my_file:
        my_file.write(books_params_json)