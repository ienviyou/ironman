from .common import InfoExtractor
from .turner import TurnerBaseIE
from ..utils import merge_dicts, try_call, url_basename


class CNNIE(TurnerBaseIE):
    _VALID_URL = r'''(?x)https?://(?:(?P<sub_domain>edition|www|money)\.)?cnn\.com/(?:video/(?:data/.+?|\?)/)?videos?/
        (?P<path>.+?/(?P<title>[^/]+?)(?:\.(?:[a-z\-]+)|(?=&)))'''

    _TESTS = [{
        'url': 'http://edition.cnn.com/video/?/video/sports/2013/06/09/nadal-1-on-1.cnn',
        'md5': '3e6121ea48df7e2259fe73a0628605c4',
        'info_dict': {
            'id': 'sports/2013/06/09/nadal-1-on-1.cnn',
            'ext': 'mp4',
            'title': 'Nadal wins 8th French Open title',
            'description': 'World Sport\'s Amanda Davies chats with 2013 French Open champion Rafael Nadal.',
            'duration': 135,
            'upload_date': '20130609',
        },
        'expected_warnings': ['Failed to download m3u8 information'],
    }, {
        'url': 'http://edition.cnn.com/video/?/video/us/2013/08/21/sot-student-gives-epic-speech.georgia-institute-of-technology&utm_source=feedburner&utm_medium=feed&utm_campaign=Feed%3A+rss%2Fcnn_topstories+%28RSS%3A+Top+Stories%29',
        'md5': 'b5cc60c60a3477d185af8f19a2a26f4e',
        'info_dict': {
            'id': 'us/2013/08/21/sot-student-gives-epic-speech.georgia-institute-of-technology',
            'ext': 'mp4',
            'title': "Student's epic speech stuns new freshmen",
            'description': 'A Georgia Tech student welcomes the incoming freshmen with an epic speech backed by music from "2001: A Space Odyssey."',
            'upload_date': '20130821',
        },
        'expected_warnings': ['Failed to download m3u8 information'],
    }, {
        'url': 'http://www.cnn.com/video/data/2.0/video/living/2014/12/22/growing-america-nashville-salemtown-board-episode-1.hln.html',
        'md5': 'f14d02ebd264df951feb2400e2c25a1b',
        'info_dict': {
            'id': 'living/2014/12/22/growing-america-nashville-salemtown-board-episode-1.hln',
            'ext': 'mp4',
            'title': 'Nashville Ep. 1: Hand crafted skateboards',
            'description': 'md5:e7223a503315c9f150acac52e76de086',
            'upload_date': '20141222',
        },
        'expected_warnings': ['Failed to download m3u8 information'],
    }, {
        'url': 'http://money.cnn.com/video/news/2016/08/19/netflix-stunning-stats.cnnmoney/index.html',
        'md5': '52a515dc1b0f001cd82e4ceda32be9d1',
        'info_dict': {
            'id': '/video/news/2016/08/19/netflix-stunning-stats.cnnmoney',
            'ext': 'mp4',
            'title': '5 stunning stats about Netflix',
            'description': 'Did you know that Netflix has more than 80 million members? Here are five facts about the online video distributor that you probably didn\'t know.',
            'upload_date': '20160819',
        },
        'params': {
            # m3u8 download
            'skip_download': True,
        },
    }, {
        'url': 'http://cnn.com/video/?/video/politics/2015/03/27/pkg-arizona-senator-church-attendance-mandatory.ktvk',
        'only_matching': True,
    }, {
        'url': 'http://cnn.com/video/?/video/us/2015/04/06/dnt-baker-refuses-anti-gay-order.wkmg',
        'only_matching': True,
    }, {
        'url': 'http://edition.cnn.com/videos/arts/2016/04/21/olympic-games-cultural-a-z-brazil.cnn',
        'only_matching': True,
    }]

    _CONFIG = {
        # http://edition.cnn.com/.element/apps/cvp/3.0/cfg/spider/cnn/expansion/config.xml
        'edition': {
            'data_src': 'http://edition.cnn.com/video/data/3.0/video/%s/index.xml',
            'media_src': 'http://pmd.cdn.turner.com/cnn/big',
        },
        # http://money.cnn.com/.element/apps/cvp2/cfg/config.xml
        'money': {
            'data_src': 'http://money.cnn.com/video/data/4.0/video/%s.xml',
            'media_src': 'http://ht3.cdn.turner.com/money/big',
        },
    }

    def _extract_timestamp(self, video_data):
        # TODO: fix timestamp extraction
        return None

    def _real_extract(self, url):
        sub_domain, path, page_title = self._match_valid_url(url).groups()
        if sub_domain not in ('money', 'edition'):
            sub_domain = 'edition'
        config = self._CONFIG[sub_domain]
        return self._extract_cvp_info(
            config['data_src'] % path, page_title, {
                'default': {
                    'media_src': config['media_src'],
                },
                'f4m': {
                    'host': 'cnn-vh.akamaihd.net',
                },
            })


class CNNArticleIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:edition|www)\.)?cnn\.com/(?!videos?/)'

    _TESTS = [{
        'url': 'https://www.cnn.com/2024/05/31/sport/video/jadon-sancho-borussia-dortmund-champions-league-exclusive-spt-intl',
        'info_dict': {
            'id': 'jadon-sancho-borussia-dortmund-champions-league-exclusive-spt-intl-1553374-1920x1080_8000k',
            'ext': 'mp4',
            'direct': True,
            'title': 'jadon-sancho-borussia-dortmund-champions-league-exclusive-spt-intl-1553374-1920x1080_8000k',
            'timestamp': 1717148749.0,
            'upload_date': '20240531',
        },
    }, {
        'url': 'https://edition.cnn.com/2024/06/11/politics/video/inmates-vote-jail-nevada-murray-dnt-ac360-digvid',
        'info_dict': {
            'id': 'inmates-vote-jail-nevada-murray-dnt-ac360-digvid-1563291-1920x1080_8000k',
            'ext': 'mp4',
            'direct': True,
            'title': 'inmates-vote-jail-nevada-murray-dnt-ac360-digvid-1563291-1920x1080_8000k',
            'timestamp': 1718158370.0,
            'upload_date': '20240612',
        },
    }, {
        'url': 'https://www.cnn.com/2024/06/11/style/video/king-charles-portrait-vandalized-activists-foster-intl-digvid',
        'info_dict': {
            'id': 'king-charles-portrait-vandalized-activists-foster-intl-digvid-1562674-1920x1080_8000k',
            'ext': 'mp4',
            'direct': True,
            'title': 'king-charles-portrait-vandalized-activists-foster-intl-digvid-1562674-1920x1080_8000k',
            'timestamp': 1718116155.0,
            'upload_date': '20240611',
        },
    }]

    def _real_extract(self, url):
        webpage = self._download_webpage(url, url_basename(url))
        cnn_url = self._search_regex(r'"@type":"VideoObject","contentUrl":"(.*?)"', webpage, 'content URL')
        if (cnn_url):
            return self.url_result(cnn_url, 'Generic')
        else:
            return self.url_result(url, CNNIE.ie_key())


class CNNIndonesiaIE(InfoExtractor):
    _VALID_URL = r'https?://www\.cnnindonesia\.com/[\w-]+/(?P<upload_date>\d{8})\d+-\d+-(?P<id>\d+)/(?P<display_id>[\w-]+)'
    _TESTS = [{
        'url': 'https://www.cnnindonesia.com/ekonomi/20220909212635-89-845885/alasan-harga-bbm-di-indonesia-masih-disubsidi',
        'info_dict': {
            'id': '845885',
            'ext': 'mp4',
            'description': 'md5:e7954bfa6f1749bc9ef0c079a719c347',
            'upload_date': '20220909',
            'title': 'Alasan Harga BBM di Indonesia Masih Disubsidi',
            'timestamp': 1662859088,
            'duration': 120.0,
            'thumbnail': r're:https://akcdn\.detik\.net\.id/visual/2022/09/09/thumbnail-ekopedia-alasan-harga-bbm-disubsidi_169\.jpeg',
            'tags': ['ekopedia', 'subsidi bbm', 'subsidi', 'bbm', 'bbm subsidi', 'harga pertalite naik'],
            'age_limit': 0,
            'release_timestamp': 1662859088,
            'release_date': '20220911',
            'uploader': 'Asfahan Yahsyi',
        },
    }, {
        'url': 'https://www.cnnindonesia.com/internasional/20220911104341-139-846189/video-momen-charles-disambut-meriah-usai-dilantik-jadi-raja-inggris',
        'info_dict': {
            'id': '846189',
            'ext': 'mp4',
            'upload_date': '20220911',
            'duration': 76.0,
            'timestamp': 1662869995,
            'description': 'md5:ece7b003b3ee7d81c6a5cfede7d5397d',
            'thumbnail': r're:https://akcdn\.detik\.net\.id/visual/2022/09/11/thumbnail-video-1_169\.jpeg',
            'title': 'VIDEO: Momen Charles Disambut Meriah usai Dilantik jadi Raja Inggris',
            'tags': ['raja charles', 'raja charles iii', 'ratu elizabeth', 'ratu elizabeth meninggal dunia', 'raja inggris', 'inggris'],
            'age_limit': 0,
            'release_date': '20220911',
            'uploader': 'REUTERS',
            'release_timestamp': 1662869995,
        },
    }]

    def _real_extract(self, url):
        upload_date, video_id, display_id = self._match_valid_url(url).group('upload_date', 'id', 'display_id')
        webpage = self._download_webpage(url, display_id)

        json_ld_list = list(self._yield_json_ld(webpage, display_id))
        json_ld_data = self._json_ld(json_ld_list, display_id)
        embed_url = next(
            json_ld.get('embedUrl') for json_ld in json_ld_list if json_ld.get('@type') == 'VideoObject')

        return merge_dicts(json_ld_data, {
            '_type': 'url_transparent',
            'url': embed_url,
            'upload_date': upload_date,
            'tags': try_call(lambda: self._html_search_meta('keywords', webpage).split(', ')),
        })
