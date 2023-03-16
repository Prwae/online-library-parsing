import requests
import os


os.makedirs("books", exist_ok=True)

for book_id in range(1, 10):
    url = f"https://tululu.org/txt.php?id={book_id}"
    response = requests.get(url)
    response.raise_for_status()

    with open(f"books/text{book_id}.txt", "wb") as file:
        file.write(response.content)
