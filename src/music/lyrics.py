from typing import Tuple

from bs4 import BeautifulSoup
from googlesearch import search
from mechanize import Browser
from ytmusicapi import YTMusic


def youtube_lyrics(youtube_id: str) -> Tuple[str, str]:
    """Gets lyrics (if exists) given the youtube id.
    NOTE: get_lyrics operation is wasteful as it discards a watch playlist while getting lyrics."""
    ytmusic = YTMusic()
    # TODO: Make more efficent use of watch_playlist
    watch_playlist = ytmusic.get_watch_playlist(videoId=youtube_id)

    browse_id = watch_playlist["lyrics"]
    if browse_id:
        result = ytmusic.get_lyrics(browse_id)
        return result["lyrics"], result["source"]

    song_name = watch_playlist["tracks"][0]["title"]
    song_artist = watch_playlist["tracks"][0]["artists"][0]["name"]

    return musixmatch_lyrics(song_name, song_artist)


def musixmatch_lyrics(song_name: str, song_artist: str) -> Tuple[str]:
    if song_name is None and song_artist is None:
        return None, None

    site = None
    musixmatch_lyric = ""

    browser = Browser()
    enable_web_scrapper(browser)
    results = search("Musixmatch.com " + song_artist + " " + song_name)

    for result in results:
        if (
            result[:27] == "https://www.musixmatch.com/"
            and result[:33] != "https://www.musixmatch.com/album/"
        ):
            site = result
            break

    if site is not None:

        browser.open(site)

        inspect_element = str(
            BeautifulSoup(browser.response().read(), "html.parser")
        )
        if "lyrics__content__ok" in inspect_element:
            musixmatch_lyric, musixmatch_source = get_web_lyric(
                inspect_element, "lyrics__content__ok"
            )
        elif "lyrics__content__warning" in inspect_element:
            musixmatch_lyric, musixmatch_source = get_web_lyric(
                inspect_element, "lyrics__content__warning"
            )
        elif "lyrics__content__error" in inspect_element:
            musixmatch_lyric, musixmatch_source = get_web_lyric(
                inspect_element, "lyrics__content__error"
            )

        return musixmatch_lyric, musixmatch_source
    return None, None


def get_web_lyric(inspect_element: str, lyrics_type: str) -> Tuple[str, str]:

    musixmatch_lyric = ""
    musixmatch_source = "Source: MusixMatch"

    splitted_inspect_element = inspect_element.split(
        '<span class="' + lyrics_type + '">'
    )

    if len(splitted_inspect_element) == 3:
        first_half_lyric = splitted_inspect_element[1].split(
            '</span></p><div><div class="inline_video_ad_container_container">'
        )
        second_half_lyric = splitted_inspect_element[2].split(
            '</span></p></div></span><div></div><div><div class="lyrics-report" id="" style="position:relative;display:inline-block">'
        )
        musixmatch_lyric = first_half_lyric[0] + "\r\n" + second_half_lyric[0]

    elif len(splitted_inspect_element) == 2:
        truncated_lyric = splitted_inspect_element[1].split("</span>")
        musixmatch_lyric = truncated_lyric[0]

    elif len(splitted_inspect_element) == 1:
        splitted_inspect_element = inspect_element.split(
            "col-xs-6 col-sm-6 col-md-6 col-ml-6 col-lg-6"
        )
        for line_index in range(3, len(splitted_inspect_element), 2):
            musixmatch_lyric = (
                str(musixmatch_lyric)
                + "\r\n"
                + splitted_inspect_element[line_index][16:-24]
            )

    if musixmatch_lyrics == "":
        return None, None

    return musixmatch_lyric, musixmatch_source


def enable_web_scrapper(browser: Browser) -> None:
    browser.set_handle_robots(False)
    browser.addheaders = [
        ("Referer", "https://www.reddit.com"),
        (
            "User-agent",
            "Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1",
        ),
    ]
