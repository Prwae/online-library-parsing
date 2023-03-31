import logging
import requests
import os
from bs4 import BeautifulSoup
import lxml
from pathvalidate import sanitize_filename


class ErrRedirection(Exception):
    pass


def check_for_redirect(response):
    if response.url == "https://tululu.org/":
        raise ErrRedirection


def download_txt(url, filename, folder='books/'):
    response = requests.get(url)
    response.raise_for_status()

    book_path = f"{os.path.join(folder, sanitize_filename(filename))}.txt"
    os.makedirs(folder, exist_ok=True)

    check_for_redirect(response)
    with open(book_path, "wb") as file:
        file.write(response.content)

    return book_path


def webpage_parsing(response):
    soup = BeautifulSoup(response.text, "lxml")
    title_tag = soup.find("h1")
    title_text = title_tag.text
    splitted_title = title_text.strip().split("::")

    title = splitted_title[0].strip()
    author = splitted_title[1].strip()

    return title, author


if __name__ == "__main__":
    for book_id in range(1, 10):
        url = f"https://tululu.org/b{book_id}"
        txt_url = f"https://tululu.org/txt.php?id={book_id}"
        response = requests.get(url)
        response.raise_for_status()
        
        try:
            check_for_redirect(response)
            title, author = webpage_parsing(response)
            download_txt(txt_url, f"{book_id}. {title}")
        except ErrRedirection:
            logging.warning("Было перенаправление")
