from canonicalwebteam.blog.common_view_logic import BlogViews
from django.conf import settings
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import redirect, render

tag_ids = settings.BLOG_CONFIG["TAG_IDS"]
excluded_tags = settings.BLOG_CONFIG["EXCLUDED_TAGS"]
blog_title = settings.BLOG_CONFIG["BLOG_TITLE"]
tag_name = settings.BLOG_CONFIG["TAG_NAME"]

blog_views = BlogViews(tag_ids, excluded_tags, blog_title, tag_name)


def index(request):
    page_param = int(request.GET.get("page", default="1"))

    context = blog_views.get_index(page=page_param)

    return render(request, "blog/index.html", context)


def latest_article(request):
    context = blog_views.get_latest_article()

    return redirect("article", slug=context.get("article").get("slug"))


def group(request, slug, template_path):
    page_param = int(request.GET.get("page", default="1"))
    category_param = request.GET.get("category", default="")

    context = blog_views.get_group(slug, page_param, category_param)

    return render(request, template_path, context)


def topic(request, slug, template_path):
    page_param = int(request.GET.get("page", default="1"))

    context = blog_views.get_topic(slug, page_param)

    return render(request, template_path, context)


def upcoming(request):
    page_param = int(request.GET.get("page", default="1"))

    context = blog_views.get_upcoming(page_param)

    return render(request, "blog/upcoming.html", context)


def author(request, username):
    page_param = int(request.GET.get("page", default="1"))

    context = blog_views.get_author(username, page_param)

    if not context:
        raise Http404("Author not found")

    return render(request, "blog/author.html", context)


def archives(request, template_path="blog/archives.html"):
    page = int(request.GET.get("page", default="1"))
    group = request.GET.get("group", default="")
    month = request.GET.get("month", default="")
    year = request.GET.get("year", default="")
    category_param = request.GET.get("category", default="")

    context = blog_views.get_archives(
        page, group, month, year, category_param
    )

    return render(request, template_path, context)


def feed(request, tags_exclude=[], tags=[], title=blog_title, subtitle=""):
    feed = blog_views.get_feed(
        request.build_absolute_uri(),
        tags_exclude=tags_exclude,
        tags=tags,
        title=title,
        subtitle=subtitle,
    )

    return HttpResponse(feed, status=200, content_type="txt/xml")


def article_redirect(request, slug, year=None, month=None, day=None):
    return redirect("article", slug=slug)


def article(request, slug):
    context = blog_views.get_article(slug)

    if not context:
        raise Http404("Article not found")

    return render(request, "blog/article.html", context)


def latest_news(request):
    context = blog_views.get_latest_news()

    return JsonResponse(context)


def tag(request, slug):
    page_param = int(request.GET.get("page", default="1"))

    context = blog_views.get_tag(slug, page_param)

    return render(request, "blog/tag.html", context)
