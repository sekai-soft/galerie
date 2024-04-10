# RSS Waterfall
一款 Pinterest/小红书照片墙式的 RSS 阅读器

[![en](https://img.shields.io/badge/lang-en-blue.svg)](https://github.com/sekai-soft/rss-waterfall/blob/master/README.md)
[![zh](https://img.shields.io/badge/中文文档-red.svg)](https://github.com/sekai-soft/rss-waterfall/blob/master/README.zh.md)
[![zh](https://img.shields.io/badge/docker-amd64-orange)](https://github.com/sekai-soft/rss-waterfall/pkgs/container/rss-waterfall)
[![zh](https://img.shields.io/badge/docker-arm64-teal)](https://github.com/sekai-soft/rss-waterfall/pkgs/container/rss-waterfall)

<img src="./screenshot.png" alt="程序截图" width="768"/>

## 功能
* 支持与 Fever API 兼容的自托管 RSS 聚合器
    * [Miniflux](https://miniflux.app/docs/fever.html)
    * [FreshRSS](https://freshrss.github.io/FreshRSS/en/users/06_Mobile_access.html)
    * [Tiny Tiny RSS (通过第三方插件)](https://github.com/DigitalDJ/tinytinyrss-fever-plugin)
* 以照片墙形式查看未读 RSS 项目中的图片
* 查看完成后将所有项目标记为已读
* （可选）连接到 Pocket ，双击图片即可快速将项目添加至稍后阅读

## 尚未实现的想法
如果觉得可以有的话，请在 issue 上评论或者打心 😀
* [公共实例（无需自己运行服务器）](https://github.com/sekai-soft/rss-waterfall/issues/2)
* [支持其他 RSS 聚合器（包括非自托管的，例如 Inoreader 和 Feedly）](https://github.com/sekai-soft/rss-waterfall/issues/1)

## 运行你自己的服务器
Docker 镜像是 `ghcr.io/sekai-soft/rss-waterfall:latest` ，并且 x86-64 和 arm64 都可用

以下是该容器接受的环境变量
| 名称                  | 必要 | 评论                                                                          |
| --------------------- | ---- | ----------------------------------------------------------------------------- |
| `FEVER_ENDPOINT`      | 是   | Fever API 的 URL 节点。如果不确定，请查看 [Fever 节点示例](#fever-节点示例)。 |
| `FEVER_USERNAME`      | 是   | Fever API 的用户名                                                            |
| `FEVER_PASSWORD`      | 是   | Fever API 的密码                                                              |
| `POCKET_CONSUMER_KEY` | 否   | 用于连接Pocket选项。查阅 ["连接 Pocket" 部分](#连接-pocket)。                 |
| `POCKET_ACCESS_TOKEN` | 否   | 用于连接Pocket选项。查阅 ["连接 Pocket" 部分](#连接-pocket)。                 |
| `PORT`                | 否   | 服务器绑定的端口。默认为 `5000`。                                             |

以下是 `docker-compose.yml` 文件示例
```yml
services:
    rss-waterfall:
    image: ghcr.io/sekai-soft/rss-waterfall:latest
    container_name: rss-waterfall
    environment:
      - PORT=80
      - FEVER_ENDPOINT=http://miniflux/fever
      - FEVER_USERNAME=miniflux
      - FEVER_PASSWORD=test123
      - POCKET_CONSUMER_KEY=
      - POCKET_ACCESS_TOKEN=
    restart: unless-stopped
```

### Fever 节点示例
首先确保你已经给你的 RSS 聚合器设置过了 Fever API 兼容

* [Miniflux](https://miniflux.app/docs/fever.html)
* [FreshRSS](https://freshrss.github.io/FreshRSS/en/users/06_Mobile_access.html)
* [Tiny Tiny RSS (通过第三方插件)](https://github.com/DigitalDJ/tinytinyrss-fever-plugin)

以下是示例的 Fever API 节点
* Miniflux: `https://miniflux.example.net/fever`
* FreshRSS: `https://freshrss.example.net/api/fever.php`
* Tiny Tiny RSS `https://tt-rss.example.net/tt-rss/plugins.local/fever/`

### 连接 Pocket
1. 在 [这里](https://getpocket.com/developer/apps/new) 创建一个新的 Pocket 开发者应用
    * 确保这个应用至少具有 "Add" 权限
2. 前往 [My Apps](https://getpocket.com/developer/apps/) 并点击你刚刚创建的开发者应用
3. 复制 Consumer Key。这将是你的 `POCKET_CONSUMER_KEY` 。
4. 前往 [这个网站](https://reader.fxneumann.de/plugins/oneclickpocket/auth.php) 获取 Access token。这将是你的 `POCKET_ACCESS_TOKEN`。
