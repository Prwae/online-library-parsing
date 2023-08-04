import argparse
import json
import logging
import time
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from general_functions import check_for_redirect, parse_book_page, download_txt, download_image, ErrRedirection, \
    TULULU_BASE_URL


def parse_book_paths(response):
    soup = BeautifulSoup(response.text, "lxml")
    book_tags = soup.find_all("table", class_="d_book")
    book_paths = [book_tag.find("a")["href"] for book_tag in book_tags]
    return book_paths


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Программа парсит книги в категории Sci-Fi на сайте Tululu.org")
    parser.add_argument("--start_page", help="С какой страницы сайта начать парсинг библиотеки", type=int, default=1)
    parser.add_argument("--end_page", help="На какой странице сайта закончить парсинг библиотеки", type=int, default=701)
    parser.add_argument("--skip_imgs", action="store_true", help="При вызове, обложки скачиваться не будут")
    parser.add_argument("--skip_txt", action="store_true", help="При вызове, тексты книг скачиваться не будут")
    parser.add_argument("--dest_folder", help="Папка с результатами парсинга, по умолчанию - results", type=str, default="results/")
    args = parser.parse_args()
    start_page = args.start_page
    end_page = args.end_page
    is_imgs_skip = args.skip_imgs
    is_txt_skip = args.skip_txt
    dest_folder = args.dest_folder

    books_params = []

    for page_num in range(start_page, end_page):
        try:
            response = requests.get(urljoin("https://tululu.org/l55/", str(page_num)))
            response.raise_for_status()
            check_for_redirect(response)

            for book_path in parse_book_paths(response):
                book_url = urljoin(TULULU_BASE_URL, f'{book_path}')
                book_id = "".join(c for c in book_path if c.isdigit())
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