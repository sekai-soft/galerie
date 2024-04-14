I18N = {
    "zh": {
        "Login | RSS Waterfall": "登录 | RSS 瀑布流",
        "A Pinterest/Xiaohongshu photo wall style RSS reader": "一款 Pinterest/小红书照片墙式的 RSS 阅读器",
        "Please login first": "请先登录",
        "Endpoint URL": "节点 URL",
        "https://github.com/sekai-soft/rss-waterfall?tab=readme-ov-file#example-fever-endpoints": "https://github.com/sekai-soft/rss-waterfall/blob/master/README.zh.md#fever-%E8%8A%82%E7%82%B9%E7%A4%BA%E4%BE%8B",
        "What is this?": "这是什么？",
        "Username": "用户名",
        "Password": "密码",
        "Login": "登录",
    }
}


def get_string(en_string: str, lang: str) -> str:
    return I18N.get(lang, {}).get(en_string, en_string)

LOGIN_TEMPLATE = """<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="X-UA-Compatible" content="ie=edge">
        <title>LOGIN_RSS_WATERFALL</title>
        <meta name="description" content="A_PINTEREST_XIAOHONGSHU_PHOTO_WALL_STYLE_RSS_READER">
        <link rel="icon" type="image/png" href="URL_FOR_FAVICON_PNG">
        <link rel="stylesheet" type="text/css" href="URL_FOR_STYLE_CSS">
        <script src="https://cdn.jsdelivr.net/npm/htmx.org@1.9.11/dist/htmx.min.js"></script>
        <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.13.8/dist/cdn.min.js"></script>
    </head>
    <body>
        <div class="stream">
            <p>PLEASE_LOGIN_FIRST</p>
            <form>
                <p>ENDPOINT_URL <a href="ENDPOINT_URL_HELP_URL" target="_blank" style="font-size: 0.5em;">WHAT_IS_THIS</a></p>
                <input
                    type="text"
                    name="endpoint"
                    required
                    placeholder="https://miniflux.example.net/fever"
                    class="code-font"
                >
                <p>USERNAME</p>
                <input
                    type="text"
                    autocomplete="username"
                    name="username"
                    required
                    class="code-font"
                    required
                >
                <p>PASSWORD</p>
                <input
                    type="password"
                    name="password"
                    required
                    class="code-font"
                >
                <div
                    class="button"
                    style="margin-top: 2em; width: 50%"
                    hx-post="/auth"
                    hx-swap="none"
                    hx-disabled-elt="this"
                >
                    LOGIN <span class="htmx-indicator">...</span>
                </div>
            </form>
        </div>
        <script>
            document.body.addEventListener("showMessage", (event) => {
                alert(event.detail.value);            
            })
        </script>
    </body>
</html>
"""


def render_login(url_for_style_css: str, url_for_favicon_png: str, lang: str):
    return LOGIN_TEMPLATE \
        .replace('LOGIN_RSS_WATERFALL', get_string('Login | RSS Waterfall', lang)) \
        .replace('A_PINTEREST_XIAOHONGSHU_PHOTO_WALL_STYLE_RSS_READER', get_string('A Pinterest/Xiaohongshu photo wall style RSS reader', lang)) \
        .replace('URL_FOR_STYLE_CSS', url_for_style_css) \
        .replace('URL_FOR_FAVICON_PNG', url_for_favicon_png) \
        .replace('PLEASE_LOGIN_FIRST', get_string('Please login first', lang)) \
        .replace('ENDPOINT_URL_HELP_URL', get_string('https://github.com/sekai-soft/rss-waterfall?tab=readme-ov-file#example-fever-endpoints', lang)) \
        .replace('ENDPOINT_URL', get_string('Endpoint URL', lang)) \
        .replace('WHAT_IS_THIS', get_string('What is this?', lang)) \
        .replace('USERNAME', get_string('Username', lang)) \
        .replace('PASSWORD', get_string('Password', lang)) \
        .replace('LOGIN', get_string('Login', lang))
