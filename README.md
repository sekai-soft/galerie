# Galerie
A Pinterest/Xiaohongshu photo wall style RSS reader

[![zh](https://img.shields.io/badge/中文文档-red.svg)](https://github.com/sekai-soft/galerie/blob/master/README.zh.md)
[![zh](https://img.shields.io/badge/docker-amd64-orange)](https://github.com/sekai-soft/galerie/pkgs/container/galerie)
[![zh](https://img.shields.io/badge/docker-arm64-teal)](https://github.com/sekai-soft/galerie/pkgs/container/galerie)

<img src="./screenshot.png" alt="Screenshot of the application" width="768"/>

## Features
* Supports self-hosted RSS aggregators that is Fever API compatible
    * [Miniflux](https://miniflux.app/docs/fever.html)
    * [FreshRSS](https://freshrss.github.io/FreshRSS/en/users/06_Mobile_access.html)
    * [Tiny Tiny RSS (via a third-party plugin)](https://github.com/DigitalDJ/tinytinyrss-fever-plugin)
* View images from unread RSS items in a beautiful photo wall
* Mark all items as read when you are done
* (Optional) Connect to Pocket and quickly add items to read-it-later by double-tapping on the image

## Run your own server
The Docker image is `ghcr.io/sekai-soft/galerie:latest` and it's available in both x86-64 and arm64

Here is a table of environment variables that the container takes
| Name                  | Required | Comment                                                                                                     |
| --------------------- | -------- | ----------------------------------------------------------------------------------------------------------- |
| `FEVER_ENDPOINT`      | Yes      | URL endpoint for your Fever API. See [example Fever endpoints](#example-fever-endpoints) if you are unsure. |
| `FEVER_USERNAME`      | Yes      | Username for your Fever API                                                                                 |
| `FEVER_PASSWORD`      | Yes      | Password for your Fever API                                                                                 |
| `POCKET_CONSUMER_KEY` | No       | For connecting to Pocket optionally. See ["Connect to Pocket" section](#connect-to-pocket)                  |
| `POCKET_ACCESS_TOKEN` | No       | For connecting to Pocket optionally. See ["Connect to Pocket" section](#connect-to-pocket)                  |
| `PORT`                | No       | The port that the server binds to. Defaults to `5000`.                                                      |

Here is an example `docker-compose.yml` file
```yml
services:
    galerie:
        image: ghcr.io/sekai-soft/galerie:latest
        ports:
            - "5000:5000"
        environment:
            - FEVER_ENDPOINT=http://miniflux/fever
            - FEVER_USERNAME=miniflux
            - FEVER_PASSWORD=test123
            - POCKET_CONSUMER_KEY=
            - POCKET_ACCESS_TOKEN=
        restart: unless-stopped
```

### Example Fever endpoints
Make sure you've configured your RSS aggregator for Fever API compatibility first!

* [Miniflux](https://miniflux.app/docs/fever.html)
* [FreshRSS](https://freshrss.github.io/FreshRSS/en/users/06_Mobile_access.html)
* [Tiny Tiny RSS (via a third-party plugin)](https://github.com/DigitalDJ/tinytinyrss-fever-plugin)

Here are some example Fever API endpoints
* Miniflux: `https://miniflux.example.net/fever`
* FreshRSS: `https://freshrss.example.net/api/fever.php`
* Tiny Tiny RSS `https://tt-rss.example.net/tt-rss/plugins.local/fever/`

### Connect to Pocket
1. Create a new Pocket developer application [here](https://getpocket.com/developer/apps/new)
    * Make sure that it has "Add" permission at least
2. Go to [My Apps](https://getpocket.com/developer/apps/) and click the developer application you just created
3. Copy the Consumer Key. This will be your `POCKET_CONSUMER_KEY`.
4. Go to [this website](https://reader.fxneumann.de/plugins/oneclickpocket/auth.php) and obtain the access token. This will be your `POCKET_ACCESS_TOKEN`.

## Development
* Run server: `flask run --reload`
* Run tests: `pytest -vv`
* Translate strings
    1. Put raw English strings in code using `_(...)` and `_l(...)`
    1. Run `flask translate update`
        * See `babel.cfg` for what files are scanned
    1. Edit updated `po` files
    1. Run `flask translate compile` and restart server
