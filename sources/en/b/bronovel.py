# -*- coding: utf-8 -*-
import logging
from bs4 import Tag
from lncrawl.core.crawler import Crawler

logger = logging.getLogger(__name__)
search_url = (
    'https://bronovel.com/?s=%s&post_type=wp-manga&op=&author=&artist=&release=&adult='
)

class BroNovel(Crawler):
    base_url = 'https://bronovel.com/'

    def search_novel(self, query):
        query = query.lower().replace(' ', '+')
        soup = self.get_soup(search_url % query)

        results = []
        for tab in soup.select('.c-tabs-item__content'):
            a = tab.select_one('.post-title h3 a')
            latest = tab.select_one('.latest-chap .chapter a').text
            votes = tab.select_one('.rating .total_votes').text
            results.append(
                {
                    'title': a.text.rsplit(' ', 1)[0].strip(),
                    'url': self.absolute_url(a['href']),
                    'info': '%s | Rating: %s' % (latest, votes),
                }
            )
        # end for

        return results

    # end def

    def read_novel_info(self):
        logger.debug('Visiting %s', self.novel_url)
        soup = self.get_soup(self.novel_url)

        possible_title = soup.select_one('meta[property="og:title"]')
        assert isinstance(possible_title, Tag), 'No novel title'
        self.novel_title = possible_title['content']
        self.novel_title = self.novel_title.rsplit(' ', 1)[0].strip()
        logger.info('Novel title: %s', self.novel_title)

        # Not using meta propery because it wrong image.
        possible_image = soup.select_one('.summary_image a img')
        if possible_image:
            self.novel_cover = self.absolute_url(possible_image['data-src'])
        logger.info('Novel cover: %s', self.novel_cover)

        self.novel_author = ' '.join(
            [
                a.text.strip()
                for a in soup.select('.author-content a[href*="manga-author"]')
            ]
        )
        logger.info('%s', self.novel_author)

        self.novel_id = soup.select_one("#manga-chapters-holder")["data-id"]
        logger.info("Novel id: %s", self.novel_id)

        response = self.submit_form(self.novel_url.strip('/') + '/ajax/chapters')
        soup = self.make_soup(response)
        for a in reversed(soup.select(".wp-manga-chapter a")):
            chap_id = len(self.chapters) + 1
            vol_id = 1 + len(self.chapters) // 100
            if chap_id % 100 == 1:
                self.volumes.append({"id": vol_id})
            # end if
            self.chapters.append(
                {
                    "id": chap_id,
                    "volume": vol_id,
                    "title": a.text,
                    "url": self.absolute_url(a["href"]),
                }
            )
        # end for

    # end def

    def download_chapter_body(self, chapter):
        logger.info("Visiting %s", chapter["url"])
        soup = self.get_soup(chapter["url"])
        contents = soup.select_one("div.text-left")
        return self.cleaner.extract_contents(contents)

    # end def


# end class
