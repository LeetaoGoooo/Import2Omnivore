from typing import List
from matter import Matter
from omnivore import Omnivore

from random import randint
import logging
import random
import time
import json
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()


matter_cookie = os.getenv("matter_cookie")

matter = Matter(matter_cookie)
omnivore = Omnivore()


def take_a_rest():
    """for api rate limit 
        take a rest
    """
    rest = randint(3, 10)
    logging.info(f"take a rest for {rest}s")
    time.sleep(rest)


def get_objs_by_name(name: str, refresh=False):
    """get objects by name from local or network

    Arguments:
        name -- labels or articles

    Keyword Arguments:
        refresh -- force refresh (default: {False})

    Returns:
        objs
    """
    fun_maps = {'labels': omnivore.get_labels, "articles": matter.get_articles}
    file_path = f'{name}.json'
    if not refresh and Path(file_path).exists():
        with open(file_path, 'r') as f:
            objs = json.load(f)
    else:
        objs = fun_maps[name]()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(objs, f)
    return objs


def create_label(name, retry=3) -> str:
    """create label in omnivore

    Arguments:
        name -- label name

    Keyword Arguments:
        retry -- retry count if failed

    Returns:
        label id
    """
    if not retry:
        logging.error(f'label {name} creat failed!')
        return
    label = omnivore.create_label(
        name=name, color=f"#{random.randint(0, 0xFFFFFF):06x}", description="")
    if not label:
        take_a_rest()
        return create_label(name, retry=retry-1)

    return label["id"]


def set_page_labels(page_id: str, label_ids: List[str], retry=3) -> bool:
    """set page with labels

    Arguments:
        page_id -- page_id
        label_ids -- label id list

    Keyword Arguments:
        retry -- max retry number  (default: {3})

    Returns:
        set label success or not
    """

    if not retry:
        logging.error(f"page {page_id} set labels {label_ids} faield")
        return
    if omnivore.set_labels(page_id, label_ids):
        logging.info(f"✨✨✨ page {page_id} set labels success✨✨✨")
        return True
    take_a_rest()
    return set_page_labels(page_id, label_ids, retry=retry-1)


def save_page(url, retry=3) -> str:
    """save page by url

    Arguments:
        url -- page url

    Keyword Arguments:
        retry -- max retry number (default: {3})

    Returns:
        return page id if success
    """
    if not retry:
        logging.error(f"page {url} save faield")
        return
    page_id = omnivore.save_page(url)
    if page_id:
        return page_id
    take_a_rest()
    return save_page(url, retry=retry-1)


def save_page_with_labels(article, existed_labels):
    """save page with labels

    Arguments:
        article -- matter article
        existed_labels -- labels already created in omnivore

    """

    page_id = save_page(article["url"])

    if not page_id:
        return existed_labels

    label_ids = []
    not_existed_labels = []

    page_labels = [tag["name"] for tag in article["tags"]]

    for page_label in page_labels:
        if page_label in existed_labels:
            label_ids.append(existed_labels[page_label])
        else:
            not_existed_labels.append(page_label)

    if not_existed_labels:
        for not_existed_label in not_existed_labels:
            label_id = create_label(not_existed_label)
            if label_id:
                label_ids.append(label_id)
                existed_labels[not_existed_label] = label_id

    if label_ids:
        set_page_labels(page_id, label_ids)

    return existed_labels


def sync_matter_to_omnivore(refresh=False):

    labels = get_objs_by_name('labels', refresh=refresh)

    label_maps = {label["name"]: label["id"] for label in labels}

    articles = get_objs_by_name('articles')

    for article in articles:
        if not article['tags']:
            continue
        new_label_maps = save_page_with_labels(article, label_maps)
        logging.info(
            f'new labels {set(new_label_maps.keys())-set(label_maps.keys())} created!')
        label_maps = new_label_maps


if __name__ == '__main__':
    sync_matter_to_omnivore()
