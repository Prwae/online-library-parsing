import argparse
import json
import logging
import os
import time
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
    parser.add_argument("--skip_imgs", action="store_true", help="При вызове, обложки скачиваться не будут")
    parser.add_argument("--skip_txt", action="store_true", help="При вызове, тексты книг скачиваться не будут")
    parser.add_argument("--dest_folder", help="Папка с результатами парсинга, по умолчанию - results", type=str, default="results/")
    args = parser.parse_args()
    start_id = args.start_id
    end_id = args.end_id
    is_imgs_skip = args.skip_imgs
    is_txt_skip = args.skip_txt
    dest_folder = args.dest_folder

    books_params = []

    for book_id in range(start_id, end_id):
        book_url = urljoin(TULULU_BASE_URL, f'b{book_id}')

        try:
            response = requests.get(book_url)
            response.raise_for_status()
            check_for_redirect(response)
            book_params = parse_book_page(response)

            title = book_params["title"]
            author = book_params["author"]
            image_url = book_params["image_url"]
            image_extencion = book_params["image_extension"]
            comments = book_params["comments"]
            genres = book_params["genres"]

            print(f"Название: {title} \nАвтор: {author}\n")

            if is_txt_skip:
                book_path = "-"
            else:
                book_path = download_txt(book_id, f"{book_id}. {title}", urljoin(dest_folder, "books/"))
            if is_imgs_skip:
                image_path = "-"
            else:
                image_path = download_image(image_url, f"{book_id}{image_extencion}", urljoin(dest_folder, "images/"))

            books_params.append(
                {
                    "title": title,
                    "author": author,
                    "img_src": image_path,
                    "book_src": book_path,
                    "comments": comments,
                    "genres": genres
                })
        except ErrRedirection:
            logging.warning("Было перенаправление")
        except requests.exceptions.HTTPError:
            logging.warning("Произошла ошибка при обработке страницы")
        except requests.exceptions.ConnectionError:
            logging.warning("Произошла ошибка соединения")
            time.sleep(10)
    books_params_json = json.dumps(books_params, ensure_ascii=False)
    with open(urljoin(dest_folder, "books_params.json"), "w", encoding="utf-8") as my_file:
        my_file.write(books_params_json)
