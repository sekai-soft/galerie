# Galerie
一款 Pinterest/小红书照片墙式的 RSS 阅读器

[![zh](https://img.shields.io/badge/docker-amd64-orange)](https://github.com/sekai-soft/galerie/pkgs/container/galerie)
[![zh](https://img.shields.io/badge/docker-arm64-teal)](https://github.com/sekai-soft/galerie/pkgs/container/galerie)

<img src="./screenshot.zh.png" alt="程序截图" width="768"/>

## 功能
* 支持以下 RSS 聚合器
    * 自托管的 [Miniflux](https://miniflux.app)
    * 任何兼容 Fever API 的自托管 RSS 聚合器
        * [FreshRSS](https://freshrss.github.io/FreshRSS/en/users/06_Mobile_access.html)
        * [Tiny Tiny RSS（通过第三方插件）](https://github.com/DigitalDJ/tinytinyrss-fever-plugin)
* 以照片墙形式查看未读 RSS 项目的图片
* 完成阅读后将所有项目标记为已读
* (可选) 连接到 Pocket，通过双击图片快速添加项目以便稍后阅读

## 托管实例
访问 [galerie-reader.com](https://galerie-reader.com) 并登陆您的 RSS 聚合器

## 自己运行服务器
Docker 镜像是 `ghcr.io/sekai-soft/galerie:latest`，并且 x86-64 和 arm64 都可用

Docker 镜像可以不接受任何环境变量。如果没有提供任何与 RSS 聚合器认证相关的环境变量，您需要在网页上使用您的 RSS 聚合器登录（就像托管实例一样）。

以下是容器接受的环境变量表
| 名称                  | 是否必需 | 备注                                                                                                                                        |
| --------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `MINIFLUX_ENDPOINT`   | 否       | 您的 Miniflux API 的 URL 端点。必须提供 `MINIFLUX_USERNAME` 和 `MINIFLUX_PASSWORD`。                                                        |
| `MINIFLUX_USERNAME`   | 否       | 您的 Miniflux API 用户名                                                                                                                    |
| `MINIFLUX_PASSWORD`   | 否       | 您的 Miniflux API 密码                                                                                                                      |
| `FEVER_ENDPOINT`      | 否       | 您的 Fever API 的 URL 端点。必须提供 `FEVER_USERNAME` 和 `FEVER_PASSWORD`。如果不确定，请参见 [示例 Fever 端点](#example-fever-endpoints)。 |
| `FEVER_USERNAME`      | 否       | 您的 Fever API 用户名                                                                                                                       |
| `FEVER_PASSWORD`      | 否       | 您的 Fever API 密码                                                                                                                         |
| `POCKET_CONSUMER_KEY` | 否       | 可选连接到 Pocket。请参见 ["连接到 Pocket" 部分](#connect-to-pocket)。                                                                      |
| `POCKET_ACCESS_TOKEN` | 否       | 可选连接到 Pocket。请参见 ["连接到 Pocket" 部分](#connect-to-pocket)。                                                                      |
| `PORT`                | 否       | 服务器绑定的端口。默认为 `5000`。                                                                                                           |

以下是 `docker-compose.yml` 文件示例
```yml
services:
    galerie:
        image: ghcr.io/sekai-soft/galerie:latest
        ports:
            - "5000:5000"
        environment:
            - MINIFLUX_ENDPOINT=http://miniflux
            - MINIFLUX_USERNAME=miniflux
            - MINIFLUX_PASSWORD=test123
            - POCKET_CONSUMER_KEY=
            - POCKET_ACCESS_TOKEN=
        restart: unless-stopped
```

### Fever 节点示例
首先确保您已经给您的 RSS 聚合器设置过了 Fever API 兼容

* [Miniflux](https://miniflux.app/docs/fever.html)
* [FreshRSS](https://freshrss.github.io/FreshRSS/en/users/06_Mobile_access.html)
* [Tiny Tiny RSS (通过第三方插件)](https://github.com/DigitalDJ/tinytinyrss-fever-plugin)

以下是示例的 Fever API 节点
* Miniflux: `https://miniflux.example.net/fever`
* FreshRSS: `https://freshrss.example.net/api/fever.php`
* Tiny Tiny RSS `https://tt-rss.example.net/tt-rss/plugins.local/fever/`

### 连接 Pocket
有三种方式可以连接到Pocket：

* 在托管实例中，您可以用您的 Pocket 帐户登录。
* 在自托管实例中
    * 您可以创建自己的 Pocket Develoepr App 并通过 OAuth 给自己授权
        1. 在[这里](https://getpocket.com/developer/apps/new)创建一个新的 Pocket Develoepr App
            * 确保它至少具有 "Add" 权限
        2. 访问[我的应用程序](https://getpocket.com/developer/apps/)并点击刚刚创建的 Develoepr App
        3. 复制 Consumer Key。这将是您的`POCKET_CONSUMER_KEY`。
        4. 在设置页面通过 OAuth 给自己授权
    * 您可以创建自己的 Pocket Develoepr App 并提供您自己的授权
        1. 在 [这里](https://getpocket.com/developer/apps/new) 创建一个新的 Pocket Develoepr App
            * 确保它至少具有 "Add" 权限
        2. 前往 [My Apps](https://getpocket.com/developer/apps/) 并点击您刚刚创建的 Develoepr App
        3. 复制 Consumer Key。这将是您的 `POCKET_CONSUMER_KEY` 。
        4. 前往 [这个网站](https://reader.fxneumann.de/plugins/oneclickpocket/auth.php) 获取 Access token。这将是您的 `POCKET_ACCESS_TOKEN`。
