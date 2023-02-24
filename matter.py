from typing import Dict, TypedDict, List
import requests
import time


class Article(TypedDict):
    title: str
    url: str
    tags: List[str]
    feed_date: str


class Matter:

    def __init__(self, cookie) -> None:
        self.cookie = cookie

    def get_matter_feeds_with_labels(self,  page=1):
        """export data from matter with label
        Arguments:
            cookie -- cookie in matter
        """
        url = f"https://web.getmatter.com/api/library_items/queue_feed?page={page}"
        resp = requests.get(
            url, headers={"cookie": self.cookie, "user-agent": "spider by Leetao"})
        if resp.status_code != 200:
            raise Exception(resp.status_code)
        resp_json = resp.json()
        feed = resp_json['feed']
        yield feed
        if resp_json['next']:
            time.sleep(1)
            yield from self.get_matter_feeds_with_labels(page=page+1)

    def parse_feed(self, matter_feed: Dict) -> Article:
        """parse matter feed into Article

        Arguments:
            matter_feed -- matter single feed data
        Returns:
            Article instance
        """
        content = matter_feed["content"]
        return Article(title=content["title"], url=content["url"], feed_date=content["feed_date"], tags=content["tags"])

    def get_articles(self) -> List[Article]:
        """export matter
        """
        articles = []
        for feeds_with_labels in self.get_matter_feeds_with_labels():
            for feed_with_labels in feeds_with_labels:
                article = self.parse_feed(feed_with_labels)
                articles.append(article)
        return articles
