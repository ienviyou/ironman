# coding: utf-8
from __future__ import unicode_literals

import itertools

from .common import InfoExtractor
from ..utils import (
    unified_strdate,
    urljoin,
    traverse_obj,
    int_or_none,
    mimetype2ext,
    clean_html,
    url_or_none, unified_timestamp, str_or_none,
)


class PRXBaseIE(InfoExtractor):
    PRX_BASE_URL_RE = r'https?://(?:beta\.)?prx.org/%s'

    def _call_api(self, item_id, path, query=None, fatal=True, note='Downloading CMS API JSON'):
        return self._download_json(
            urljoin('https://cms.prx.org/api/v1/', path), item_id, query=query, fatal=fatal, note=note)

    @staticmethod
    def _extract_embedded_data(response):
        return traverse_obj(response, '_embedded', expected_type=dict, default={})

    @classmethod
    def _get_prx_embed_response(cls, response, section):
        return cls._extract_embedded_data(response).get(f'prx:{section}')

    @staticmethod
    def _extract_file_link(response):
        return url_or_none(traverse_obj(
            response, ('_links', 'enclosure', 'href'), expected_type=str))

    @classmethod
    def _extract_image(cls, image_response):
        if not isinstance(image_response, dict):
            return
        return {
            'id': str(image_response.get('id')),
            'filesize': image_response.get('size'),
            'width': image_response.get('width'),
            'height': image_response.get('height'),
            'url': cls._extract_file_link(image_response)
        }

    @classmethod
    def _extract_base_info(cls, response):
        if not isinstance(response, dict):
            return
        item_id = str_or_none(response.get('id'))
        if not item_id:
            return
        thumbnail_dict = cls._extract_image(cls._get_prx_embed_response(response, 'image'))
        description = (
            clean_html(response.get('description'))
            or response.get('shortDescription'))
        return {
            'id': item_id,
            'title': response.get('title') or item_id,
            'thumbnails': [thumbnail_dict] if thumbnail_dict else None,
            'description': description,
            'release_date': unified_strdate(response.get('producedOn')),
            'timestamp': unified_timestamp(response.get('createdAt')),
            'modified_timestamp': unified_timestamp(response.get('updatedAt')),  # TODO: requires #2069
            'duration': int_or_none(response.get('duration')),
            'tags': response.get('tags'),
        }

    @classmethod
    def _extract_series_info(cls, series_response):
        base_info = cls._extract_base_info(series_response)
        if not base_info:
            return
        account_info = cls._extract_account_info(
            cls._get_prx_embed_response(series_response, 'account')) or {}
        return {
            **base_info,
            'channel_id': account_info.get('channel_id'),
            'channel_url': account_info.get('channel_url'),
            'channel': account_info.get('channel'),
            'series': base_info.get('title'),
            'series_id': base_info.get('id'),
        }

    @classmethod
    def _extract_account_info(cls, account_response):
        base_info = cls._extract_base_info(account_response)
        if not base_info:
            return
        name = account_response.get('name')
        return {
            **base_info,
            'title': name,
            'channel_id': base_info.get('id'),
            'channel_url': f'https://beta.prx.org/accounts/%s' % base_info.get('id'),
            'channel': name,
        }

    @classmethod
    def _extract_story_info(cls, story_response):
        base_info = cls._extract_base_info(story_response)
        if not base_info:
            return
        series = cls._extract_series_info(
            cls._get_prx_embed_response(story_response, 'series')) or {}
        account = cls._extract_account_info(
            cls._get_prx_embed_response(story_response, 'account')) or {}
        return {
            **base_info,
            'series': series.get('series'),
            'series_id': series.get('series_id'),
            'channel_id': account.get('channel_id'),
            'channel_url': account.get('channel_url'),
            'channel': account.get('channel')
        }

    def _get_entries(self, item_id, endpoint, func):
        total = 0
        for page in itertools.count(1):
            response = self._call_api(
                f'{item_id}: page {page}', endpoint, query={'page': page}) or {}
            items = self._get_prx_embed_response(response, 'items') or []

            if not (response or items):
                break

            # Below this could be generalised to support existing metadata
            for entry_response in items:
                res = func(entry_response)
                if res:
                    yield res
                total += 1

            if total >= response.get('total'):
                break

    def _story_list_response(self, entry_response):
        story = self._extract_story_info(entry_response)
        if not story:
            return
        story.update({
            '_type': 'url',
            'url': 'https://beta.prx.org/stories/%s' % story['id'],
            'ie_key': PRXStoryIE.ie_key()
        })
        return story

    def _series_list_response(self, response):
        series = self._extract_series_info(response)
        if not series:
            return
        series.update({
            '_type': 'url',
            'url': 'https://beta.prx.org/series/%s' % series['id'],
            'ie_key': PRXSeriesIE.ie_key()
        })
        return series


class PRXStoryIE(PRXBaseIE):
    _VALID_URL = PRXBaseIE.PRX_BASE_URL_RE % r'stories/(?P<id>\d+)'

    # This extract type Audio (the literal audio format)
    # TODO: there is also audio-versions type, which includes Audio types.
    #  But it may include things such as transcript?

    def _extract_audio_pieces(self, audio_response):
        # TODO: concatenate the pieces with a concat PP is implemented
        # Currently returning as multi_video for the time being
        pieces = []
        piece_response = self._get_prx_embed_response(audio_response, 'items') or []
        piece_response.sort(key=lambda x: int_or_none(x.get('position')))
        for piece_response in self._get_prx_embed_response(audio_response, 'items'):
            pieces.append({
                'format_id': str(piece_response.get('id')),
                'filesize': int_or_none(piece_response.get('size')),
                'duration': int_or_none(piece_response.get('duration')),
                'ext': mimetype2ext(piece_response.get('contentType')),
                'asr': int_or_none(piece_response.get('frequency'), scale=1000),
                'abr': int_or_none(piece_response.get('bitRate')),
                'url': self._extract_file_link(piece_response),
                'vcodec': 'none',
            })
        return pieces

    # TODO: checks for if we have a full story/series response, how many pages etc.
    def _extract_story(self, story_response):
        info = self._extract_story_info(story_response)
        if not info:
            return
        entries = []
        audio_pieces = self._extract_audio_pieces(
            self._get_prx_embed_response(story_response, 'audio'))
        for idx, fmt in enumerate(audio_pieces):
            entries.append({
                '_type': 'video',
                **info,  # needs to be before id to override
                'id': '%s_part%d' % (info['id'], (idx + 1)),
                'formats': [fmt],
            })
        return {
            '_type': 'multi_video',
            'entries': entries,
            **info
        }

    def _real_extract(self, url):
        story_id = self._match_id(url)
        response = self._call_api(story_id, f'stories/{story_id}')
        story = self._extract_story(response)
        return story


class PRXSeriesIE(PRXBaseIE):
    _VALID_URL = PRXBaseIE.PRX_BASE_URL_RE % r'series/(?P<id>\d+)'
    _TESTS = [
        {
            # Blank series
            'url': 'https://beta.prx.org/series/25038',
            'info_dict': {
                'id': '25038',
                'title': '25038'
            },
            'count': 0
        }
    ]

    def _extract_series(self, series_response):
        info = self._extract_series_info(series_response)
        return {
            '_type': 'playlist',
            'entries': self._get_entries(info['id'], f'series/{info["id"]}/stories', self._story_list_response),
            **info
        }

    def _real_extract(self, url):
        series_id = self._match_id(url)
        response = self._call_api(series_id, f'series/{series_id}')
        return self._extract_series(response)


class PRXAccountIE(PRXBaseIE):
    _VALID_URL = PRXBaseIE.PRX_BASE_URL_RE % r'accounts/(?P<id>\d+)'
    _TESTS = []

    def _extract_account(self, account_response):
        info = self._extract_account_info(account_response)
        series = self._get_entries(
            info['id'], f'accounts/{info["id"]}/series', self._series_list_response)

        stories = self._get_entries(
            info['id'], f'accounts/{info["id"]}/stories', self._story_list_response)
        return {
            '_type': 'playlist',
            'entries': itertools.chain(series, stories),
            **info
        }

    def _real_extract(self, url):
        account_id = self._match_id(url)
        response = self._call_api(account_id, f'accounts/{account_id}')
        return self._extract_account(response)
