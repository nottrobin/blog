# Standard library
import html
import re
from datetime import datetime, date

# Packages
import json
import requests
from werkzeug.contrib.atom import AtomFeed

# Local
from canonicalwebteam.blog import logic
from canonicalwebteam.blog import wordpress_api as api
from canonicalwebteam.blog.http import fetch_all
from canonicalwebteam.blog.wordpress import UrlBuilder, Parser
from dateutil.relativedelta import relativedelta


EVENTS = 1175
WEBINARS = 1187
TIMEOUT = 5
CLEAN_HTML_REGEX = re.compile("<.*?>")


class BlogViews:
    def __init__(self, tag_ids, tags_exclude):
        self.urls = UrlBuilder(tags=tag_ids, tags_exclude=tags_exclude)
        self.parse = Parser(tags=tag_ids, tags_exclude=tags_exclude)

    def get_index(self, page=1, category_ids=None):
        # Queue up request for the first 12 posts
        urls = [
            self.urls.posts(
                page=page,
                per_page=12,
                categories=category_ids,
                sticky=False,
                _embed=True,
            )
        ]

        # For the first page, also get featured and upcoming posts
        if page == 1:
            urls.append(self.urls.posts(per_page=3, sticky=True, _embed=True))
            urls.append(
                self.urls.posts(
                    per_page=3, categories=[EVENTS, WEBINARS], _embed=True
                )
            )

        # Fetch all URLs, concurrently
        results = fetch_all(urls, timeout=TIMEOUT)

        # Get posts from results
        posts_response = results[0]["response"]
        posts = json.loads(results[0]["text"])

        # Get featured and upcoming posts from results
        if len(results) > 1:
            featured_posts = json.loads(results[1]["text"])
            upcoming_posts = json.loads(results[2]["text"])
        else:
            featured_posts = None
            upcoming_posts = None

        # Send everything to the template
        return {
            "current_page": page,
            "total_pages": posts_response.headers.get("x-wp-totalpages"),
            "posts": self.parse.posts(posts),
            "featured_posts": self.parse.posts(featured_posts),
            "upcoming_posts": self.parse.posts(upcoming_posts),
        }

    def get_article(self, slug):
        post

        post_info = format_post_info(post)
        post_info['content'] = replace_images_with_cloudinary(post["content"]["rendered"])

        return post_info

    def get_latest_id(self):
        response = requests.get(self.urls.posts(per_page=1), timeout=TIMEOUT)

        return response.json()[0]["slug"]

    def get_group(self, group_slug, page=1, category_slug=""):
        group = api.get_group_by_slug(group_slug)

        category = {}
        if category_slug:
            category = api.get_category_by_slug(category_slug)

        articles, metadata = api.get_articles(
            tags=self.tag_ids,
            tags_exclude=self.excluded_tags,
            page=page,
            groups=[group.get("id", "")],
            categories=[category.get("id", "")],
        )
        total_pages = metadata["total_pages"]

        context = get_group_page_context(page, articles, total_pages, group)
        context["title"] = self.blog_title
        context["category"] = {"slug": category_slug}

        return context

    def get_topic(self, topic_slug, page=1):
        tag = api.get_tag_by_slug(topic_slug)

        articles, metadata = api.get_articles(
            tags=self.tag_ids + [tag["id"]],
            tags_exclude=self.excluded_tags,
            page=page,
        )
        total_pages = metadata["total_pages"]

        context = get_topic_page_context(page, articles, total_pages)
        context["title"] = self.blog_title

        return context

    def get_upcoming(self, page=1):
        events = api.get_category_by_slug("events")
        webinars = api.get_category_by_slug("webinars")

        articles, metadata = api.get_articles(
            tags=self.tag_ids,
            tags_exclude=self.excluded_tags,
            page=page,
            categories=[events["id"], webinars["id"]],
        )
        total_pages = metadata["total_pages"]

        context = get_index_context(page, articles, total_pages)
        context["title"] = self.blog_title

        return context

    def get_author(self, username, page=1):
        author = api.get_user_by_username(username)

        if not author:
            return None

        articles, metadata = api.get_articles(
            tags=self.tag_ids,
            tags_exclude=self.excluded_tags,
            page=page,
            author=author["id"],
        )

        context = get_index_context(
            page, articles, metadata.get("total_pages")
        )
        context["title"] = self.blog_title
        context["author"] = author
        context["total_posts"] = metadata.get("total_posts", 0)

        return context

    def get_latest_news(self):
        latest_pinned_articles, _ = api.get_articles(
            tags=self.tag_ids,
            exclude=self.excluded_tags,
            page=1,
            per_page=1,
            sticky=True,
        )

        per_page = 3
        if latest_pinned_articles:
            per_page = 4

        latest_articles, _ = api.get_articles(
            tags=self.tag_ids,
            exclude=self.excluded_tags,
            page=1,
            per_page=per_page,
            sticky=False,
        )

        return {
            "latest_articles": latest_articles,
            "latest_pinned_articles": latest_pinned_articles,
        }

    def get_archives(self, page=1, group="", month="", year="", category=""):
        groups = []
        categories = []

        if group:
            group = api.get_group_by_slug(group)
            groups.append(group["id"])

        if category:
            category_slugs = category.split(",")
            for slug in category_slugs:
                category = api.get_category_by_slug(slug)
                categories.append(category["id"])

        after = None
        before = None
        if year:
            year = int(year)
            if month:
                after = datetime(year=year, month=int(month), day=1)
                before = after + relativedelta(months=1)
            else:
                after = datetime(year=year, month=1, day=1)
                before = datetime(year=year, month=12, day=31)

        articles, metadata = api.get_articles(
            tags=self.tag_ids,
            tags_exclude=self.excluded_tags,
            page=page,
            groups=groups,
            categories=categories,
            after=after,
            before=before,
        )

        total_pages = metadata["total_pages"]
        total_posts = metadata["total_posts"]

        if group:
            context = get_group_page_context(
                page, articles, total_pages, group
            )
        else:
            context = get_index_context(page, articles, total_pages)

        context["title"] = self.blog_title
        context["total_posts"] = total_posts

        return context

    def get_feed(
        self, uri, tags_exclude=[], tags=[], title="Blog", subtitle=""
    ):
        posts = api.get_feed(
            self.tag_ids + tags, tags_exclude=tags_exclude + self.excluded_tags
        )

        feed = AtomFeed(title, feed_url=uri, url=uri, subtitle=subtitle)

        for post in posts:
            last_modified = datetime.strptime(
                post["modified_gmt"], "%Y-%m-%dT%H:%M:%S"
            )
            published = datetime.strptime(
                post["modified_gmt"], "%Y-%m-%dT%H:%M:%S"
            )
            feed.add(
                post["title"]["rendered"],
                post["content"]["rendered"],
                content_type="html",
                author=post["_embedded"]["author"][0],
                url=post["link"],
                id=post["id"],
                updated=last_modified,
                published=published,
            )
        return feed.to_string()

    def get_tag(self, slug, page=1):
        tag = api.get_tag_by_slug(slug)

        articles, metadata = api.get_articles(
            tags=self.tag_ids + [tag["id"]],
            tags_exclude=self.excluded_tags,
            page=page,
        )
        total_pages = metadata["total_pages"]

        context = get_topic_page_context(page, articles, total_pages)
        context["title"] = self.blog_title
        context["tag"] = tag

        return context


def format_excerpt(post):
    # Remove any HTML
    clean_text = re.sub(CLEAN_HTML_REGEX, "", post["excerpt"]["raw"])
    raw_content = html.unescape(clean_text).replace("\n", "")[:340]

    # If the excerpt doesn't end before 340 characters, add ellipsis
    # ===

    # split at the last 3 characters
    raw_content_start = raw_content[:-3]
    raw_content_end = raw_content[-3:]

    # for the last 3 characters replace any part of […]
    raw_content_end = raw_content_end.replace("[", "")
    raw_content_end = raw_content_end.replace("…", "")
    raw_content_end = raw_content_end.replace("]", "")

    # join it back up
    return "".join([raw_content_start, raw_content_end, " […]"])


def format_post_info(post):
    """
    Parse out the most common useful info from a wordpres post response
    """

    images = post["_embedded"].get("wp:featuredmedia", [])
    start_date = None
    end_date = None

    if (
        post.get("_start_month")
        and post.get("_start_year")
        and post.get("_start_day")
    ):
        post["start_date"] = "{} {} {}".format(
            post["_start_day"],
            date(1900, int(post["_start_month"]), 1).strftime("%B"),
            post["_start_year"],
        )

    if (
        post.get("_end_month")
        and post.get("_end_year")
        and post.get("_end_day")
    ):
        post["end_date"] = "{} {} {}".format(
            post["_end_day"],
            date(1900, int(post["_end_month"]), 1).strftime("%B"),
            post["_end_year"],
        )

    return {
        "image": images[0] if images else None,
        "start_date": start_date,
        "end_date": end_date,
        "author": post["_embedded"].get("author", [{}])[0],
        "category": post["_embedded"]["wp:term"][0][0],
        "group": post["_embedded"]["wp:term"][3][0],
        "date": datetime.strptime(
            post["date_gmt"], "%Y-%m-%dT%H:%M:%S"
        ).strftime("%-d %B %Y"),
    }


def replace_images_with_cloudinary(content):
    """
    Prefixes images with cloudinary optimised URLs and adds srcset for
    image scaling

    :param content: The HTML string to convert

    :returns: Update HTML string with converted images
    """
    cloudinary = "https://res.cloudinary.com/"

    urls = [
        cloudinary + r"canonical/image/fetch/q_auto,f_auto,w_350/\g<url>",
        cloudinary + r"canonical/image/fetch/q_auto,f_auto,w_650/\g<url>",
        cloudinary + r"canonical/image/fetch/q_auto,f_auto,w_1300/\g<url>",
        cloudinary + r"canonical/image/fetch/q_auto,f_auto,w_1950/\g<url>",
    ]

    image_match = (
        r'<img(?P<prefix>[^>]*) src="(?P<url>[^"]+)"(?P<suffix>[^>]*)>'
    )
    replacement = (
        r"<img\g<prefix>"
        f' decoding="async"'
        f' src="{urls[1]}"'
        f' srcset="{urls[0]} 350w, {urls[1]} 650w, {urls[2]} 1300w,'
        f' {urls[3]} 1950w"'
        f' sizes="(max-width: 400px) 350w, 650px"'
        r"\g<suffix>>"
    )

    return re.sub(image_match, replacement, content)


def get_group_page_context(
    page_param, articles, total_pages, group, featured_articles=[]
):
    """
    Build the content for a group page
    :param page_param: String or int for index of the page to get
    :param articles: Array of articles
    :param articles: String of int of total amount of pages
    :param group: Article group
    """

    context = get_index_context(
        page_param, articles, total_pages, featured_articles
    )
    context["group"] = group

    return context


def get_topic_page_context(page_param, articles, total_pages):
    """
    Build the content for a group page
    :param page_param: String or int for index of the page to get
    :param articles: Array of articles
    :param articles: String of int of total amount of pages
    """

    return get_index_context(page_param, articles, total_pages)


def get_article_context(article, related_tag_ids=[], excluded_tags=[]):
    """
    Build the content for the article page
    :param article: Article to create context for
    """

    transformed_article = get_complete_article(article)

    tags = logic.get_embedded_tags(article["_embedded"])
    is_in_series = logic.is_in_series(tags)

    all_related_articles, _ = api.get_articles(
        tags=[tag["id"] for tag in tags],
        tags_exclude=excluded_tags,
        per_page=3,
        exclude=[article["id"]],
    )

    related_articles = []
    for related_article in all_related_articles:
        if set(related_tag_ids) <= set(related_article["tags"]):
            related_articles.append(logic.transform_article(related_article))

    return {
        "article": transformed_article,
        "related_articles": related_articles,
        "tags": tags,
        "is_in_series": is_in_series,
    }
