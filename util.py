# This Python file uses the following encoding: utf-8
# License: GPL-3 (https://choosealicense.com/licenses/gpl-3.0/)
# Original author: Killed_Mufasa

# Twitter: https://twitter.com/Killed_Mufasa
# Reddit:  https://www.reddit.com/user/Killed_Mufasa
# GitHub:  https://github.com/KilledMufasa
# Website: https://www.amputatorbot.com
# Donate:  https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=EU6ZFKTVT9VH2

# This wonderful little program is used by u/AmputatorBot (https://www.reddit.com/user/AmputatorBot)
# to perform a couple of tasks: log in, generate a random header, check for amp links,
# check for google amp links, remove markdown, getting the canonical url,

# Import a couple of libraries
import os
import re
import traceback
from random import choice

import requests
from bs4 import BeautifulSoup

warning_log = [""]

# https://github.com/KilledMufasa/AmputatorBot/blob/master/config.py
headers = [
    "Mozilla/5.0 (Linux; Android 8.0.0; SM-G960F Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3202.84 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 9; CLT-L29) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3945.116 Mobile Safari/537.36",
]


class logging:
    def error(self, *, arg):
        pass

    def warn(self, *, arg):
        pass

    def info(self, *, arg):
        pass

    def debug(self, *, arg):
        pass


def send_warning(warning):
    pass


# Get randomized user agent, set default accept and request English page
# This is done to prevent 403 errors.
def random_headers():
    return {
        "User-Agent": choice(headers),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US",
    }


def check_if_amp(string):
    string = string.lower()  # Make string lowercase

    # If the string contains an AMP link, return True
    if (
        "/amp" in string
        or "amp/" in string
        or ".amp" in string
        or "amp." in string
        or "?amp" in string
        or "amp?" in string
        or "=amp" in string
        or "amp=" in string
        or "&amp" in string
        or "amp&" in string
        and "https://" in string
    ):
        return True

    # If no AMP link was found in the string, return False
    return False


def check_if_google(string):
    string = string.lower()  # Make string lowercase

    # If the string contains an Google AMP link, return True
    if (
        "www.google." in string
        or "ampproject.net" in string
        or "ampproject.org" in string
    ):
        return True

    # If no Google AMP link was found in the string, return False
    return False


def remove_markdown(url):
    # Isolate the actual URL (remove markdown) (part 1)
    try:
        url = url.split("](")[-1]
        logging.debug("{} was stripped of this string: ']('".format(url))

    except:
        logging.error(traceback.format_exc())
        logging.debug(
            "{} couldn't or didn't have to be stripped of this string: ']('.".format(
                url
            )
        )

    # Isolate the actual URL (remove markdown) (part 2)
    if url.endswith(")?"):
        url = url[:-2]
        logging.debug("{} was stripped of this string: ')?'".format(url))

    if url.endswith("),"):
        url = url[:-2]
        logging.debug("{} was stripped of this string: ')'".format(url))

    if url.endswith(")."):
        url = url[:-2]
        logging.debug("{} was stripped of this string: ')'".format(url))

    if url.endswith(")"):
        url = url[:-1]
        logging.debug("{} was stripped of this string: ')'".format(url))

    return url


def get_canonical(og_url, depth):
    logging.info("NEW: {} with depth {}".format(og_url, depth))
    # Check if the URL is an AMP URL

    next_url = og_url
    og_depth = depth

    i = 0
    # Try for every AMP link, until the max is reached
    while i < depth:
        # Get the HTML content of the webpage
        soup = get_soup(next_url)
        # Try to find the canonical with rel=canonical
        found_canonical_link, is_solved = get_canonical_with_rel(soup, og_url)

        # If the canonical url returned is not AMP, save and return it
        if is_solved:
            logging.info("SUCCESS: Found canonical with rel: " + found_canonical_link)

            return found_canonical_link

        # If the canonical returned is still AMP, try again with canurl
        if not found_canonical_link:
            found_canonical_link_alt1, is_solved_alt1 = get_canonical_with_canurl(
                soup, og_url
            )

            # If the canonical url returned is not AMP, save and return it
            if is_solved_alt1:
                logging.info(
                    "SUCCESS: Found canonical with canurl: " + found_canonical_link_alt1
                )
                return found_canonical_link_alt1

            # If the canonical returned is still AMP, prepare the next run
            if found_canonical_link_alt1:
                next_url = found_canonical_link_alt1

            # If the canonical returned is still AMP, try again with redirect
            if not found_canonical_link and not found_canonical_link_alt1:
                found_canonical_link_alt2, is_solved_alt2 = get_canonical_with_redirect(
                    soup, og_url
                )

                # If the canonical url is not AMP, save and return it
                if is_solved_alt2:
                    logging.info(
                        "SUCCESS: Found canonical with redirect: "
                        + found_canonical_link_alt2
                    )
                    return found_canonical_link_alt2

                # If the canonical returned is still AMP, prepare the next run
                if found_canonical_link_alt2:
                    next_url = found_canonical_link_alt2

                # If no canonical link was found whatsoever, save the error and return None
                if (
                    not found_canonical_link
                    and not found_canonical_link_alt1
                    and not found_canonical_link_alt2
                ):
                    return None

        if found_canonical_link:
            next_url = found_canonical_link

        logging.info("next_url = " + next_url)

        depth = depth - 1

    if og_depth < 2:
        logging.info("Consider increasing the maximum amount of referrals below")
    send_warning("Couldn't find any canonical links with this depth")
    return None


def get_canonical_with_rel(soup, url):
    # Get all canonical links in a list using rel
    try:
        canonical_links = soup.find_all(rel="canonical")
        if canonical_links:
            for link in canonical_links:
                # Get the direct link
                found_canonical_url = link.get("href")
                # If the canonical url is the submitted url, don't use it
                if found_canonical_url == url:
                    send_warning("Encountered a false positive")
                else:
                    if not check_if_amp(found_canonical_url):
                        return found_canonical_url, True
                    else:
                        return found_canonical_url, False

        send_warning("Couldn't find any canonical links")
        return None, False
    except:
        send_warning("Couldn't scrape the website")
        return None, False


def get_canonical_with_canurl(soup, url):
    # Get all canonical links in a list using rel
    try:
        canonical_links = soup.find_all(a="amp-canurl")
        if canonical_links:
            for a in canonical_links:
                # Get the direct link
                found_canonical_url = a.get("href")
                # If the canonical url is the submitted url, don't use it
                if found_canonical_url == url:
                    send_warning("Encountered a false positive")
                else:
                    if not check_if_amp(found_canonical_url):
                        return found_canonical_url, True
                    else:
                        return found_canonical_url, False

        send_warning("Couldn't find any canonical links")
        return None, False
    except:
        send_warning("Couldn't scrape the website")


def get_canonical_with_redirect(soup, url):
    try:
        content = soup.get_text().lower()
        # Try to detect if the page has a Redirect Notice
        if (
            "redirect notice" in content
            or "The page you were on is trying to send you to" in content
        ):
            send_warning("Had to follow a redirect")
            redirect_link = soup.find_all("a")[0].get("href")

            if redirect_link == url:
                send_warning("Encountered a false positive")
            else:
                if not check_if_amp(redirect_link):
                    logging.info("Found the canonical with redirect:" + redirect_link)
                    return redirect_link, True
                else:
                    send_warning(
                        "Found the canonical with redirect, but it's still AMP: "
                        + redirect_link
                    )
                    return redirect_link, False

            # If there was a redirect notice found, but no canonical url, log the soup for debugging purposes
            logging.info(
                "Couldn't find the canonical URL with redirect of "
                + url
                + ", soup: "
                + content
            )
            return None, False

        # If there is no redirect, log the soup for debugging purposes
        else:
            return None, False
    except:
        return None, False


def get_soup(url):
    try:
        # Fetch amp page
        logging.info("Started fetching " + url)
        req = requests.get(url, headers=random_headers())

        # Make the received data searchable
        logging.info("Making a soup..")
        soup = BeautifulSoup(req.text, features="lxml")
        return soup

    # If the submitted page couldn't be fetched, throw an exception
    except:
        logging.error(traceback.format_exc())
        send_warning(
            "the page could not be fetched (the website is probably blocking bots or geo-blocking)"
        )
        return None


def get_amp_urls(item_body):
    # Scan the item body for the links
    item_urls = re.findall("(?P<url>https?://[^\s]+)", item_body)
    amp_urls = []
    # Loop through all found links
    for x in range(len(item_urls)):
        # Remove the markdown from the URL
        item_urls[x] = remove_markdown(item_urls[x])

        # Check: Is the isolated URL really an amp link?
        if check_if_amp(item_urls[x]):
            logging.debug("\nAn amp link was found: {}".format(item_urls[x]))
            amp_urls.append(item_urls[x])

        # If the program fails to get the correct amp link, ignore it.
        else:
            logging.warning("This link is no AMP link: {}\n".format(item_urls[x]))

    return amp_urls


def get_canonicals(amp_urls, use_markdown):
    canonical_urls = []
    canonical_urls_clean = []
    for x in range(len(amp_urls)):
        canonical_url = get_canonical(amp_urls[x], 3)
        if canonical_url is not None:
            logging.debug("Canonical_url returned is not None")
            canonical_urls_clean.append(canonical_url)
            # Add markdown in case there are multiple URLs
            if use_markdown:
                # Calculate which number to prefix
                canonical_urls_amount = len(canonical_urls) + 1
                # Make a string out of the prefix and the canonical url
                canonical_url_markdown = (
                    "["
                    + str(canonical_urls_amount)
                    + "] **["
                    + canonical_url
                    + "]("
                    + canonical_url
                    + ")**"
                )
                # And append this to the list
                canonical_urls.append(canonical_url_markdown)
                logging.debug(
                    "The array of canonical urls is now: {}".format(canonical_urls)
                )
            else:
                # And append this to the list
                canonical_urls.append(canonical_url)
                logging.debug(
                    "The array of canonical urls is now: {}".format(canonical_urls)
                )
        else:
            logging.debug("No canonical URLs were found, skipping this one")

    if len(canonical_urls_clean) == 1:
        return canonical_urls_clean

    return canonical_urls
