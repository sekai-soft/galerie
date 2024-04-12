LOGIN_TEMPLATE = """<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="X-UA-Compatible" content="ie=edge">
        <title>Login | RSS Waterfall</title>
        <meta name="description" content="A Pinterest/Xiaohongshu photo wall style RSS reader">
        <link rel="stylesheet" type="text/css" href="URL_FOR_STYLE_CSS">
        <script src="https://unpkg.com/htmx.org@1.9.11/dist/htmx.js" integrity="sha384-l9bYT9SL4CAW0Hl7pAOpfRc18mys1b0wK4U8UtGnWOxPVbVMgrOdB+jyz/WY8Jue" crossorigin="anonymous"></script>
        <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.13.8/dist/cdn.min.js"></script>
    </head>
    <body>
        <div class="stream">
            <p>Please login first</p>
            <form>
                <p>Endpoint URL <a href="https://github.com/sekai-soft/rss-waterfall?tab=readme-ov-file#example-fever-endpoints" target="_blank" style="font-size: 0.5em;">What is this?</a></p>
                <input
                    type="text"
                    name="endpoint"
                    required
                    placeholder="https://miniflux.example.net/fever"
                    class="code-font"
                >
                <p>Username</p>
                <input
                    type="text"
                    autocomplete="username"
                    name="username"
                    required
                    class="code-font"
                    required
                >
                <p>Password</p>
                <input
                    type="password"
                    name="password"
                    required
                    class="code-font"
                >
                <div
                    class="button"
                    style="margin-top: 2em"
                    hx-post="/auth"
                    hx-swap="none"
                >
                    Login <span class="htmx-indicator">...</span>
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


def render_login(url_for_style_css: str):
    return LOGIN_TEMPLATE.replace('URL_FOR_STYLE_CSS', url_for_style_css)
