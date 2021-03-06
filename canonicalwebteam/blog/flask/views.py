import flask

from canonicalwebteam.blog import wordpress_api as api
from canonicalwebteam.blog import logic
from canonicalwebteam.blog.common_view_logic import (
    get_index_context,
    get_article_context,
)


def build_blueprint(blog_title, tags_id, tag_name):
    blog = flask.Blueprint(
        "blog", __name__, template_folder="/templates", static_folder="/static"
    )

    @blog.route("/")
    def homepage():
        page_param = flask.request.args.get("page", default=1, type=int)

        try:
            articles, total_pages = api.get_articles(
                tags=tags_id, page=page_param
            )
        except Exception:
            return flask.abort(502)

        context = get_index_context(page_param, articles, total_pages)

        return flask.render_template("blog/index.html", **context)

    @blog.route("/feed")
    def feed():
        try:
            feed = api.get_feed(tag_name)
        except Exception as e:
            print(e)
            return flask.abort(502)

        right_urls = logic.change_url(
            feed, flask.request.base_url.replace("/feed", "")
        )

        right_title = right_urls.replace("Ubuntu Blog", blog_title)

        return flask.Response(right_title, mimetype="text/xml")

    @blog.route(
        '/<regex("[0-9]{4}"):year>/<regex("[0-9]{2}"):month>/'
        '<regex("[0-9]{2}"):day>/<slug>'
    )
    @blog.route('/<regex("[0-9]{4}"):year>/<regex("[0-9]{2}"):month>/<slug>')
    @blog.route('/<regex("[0-9]{4}"):year>/<slug>')
    def article_redirect(slug, year, month=None, day=None):
        return flask.redirect(flask.url_for(".article", slug=slug))

    @blog.route("/<slug>")
    def article(slug):
        try:
            articles = api.get_article(tags_id, slug)
        except Exception:
            return flask.abort(502)

        if not articles:
            flask.abort(404, "Article not found")

        context = get_article_context(articles)

        return flask.render_template("blog/article.html", **context)

    return blog
