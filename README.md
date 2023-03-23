# Interactive Crawler - 交互式WEB网站爬虫

> ​		Interactive Crawl是一款交互式爬虫工具，不仅可以爬取页面中的超链接，还能获取通过页面的各种交互事件触发所发起的请求，支持代理设置，可结合其他漏洞扫描工具使用。目前支持以下事件的触发：
>
> - [x] Form表单；
> - [x] 各种标签的onclick事件；
> - [x] a标签内的JavaScript代码;
> - [ ] 增加下拉列表等隐藏式交互事件触发；
> - [ ] 增加不带有onclick属性的按钮交互事件触发；
> - [ ] 其他;

## Installation

```bash
# 下载项目
git clone https://github.com/ITNAX/Interactive-Crawl.git
# 安装python依赖包
pip install -r requirements.txt
# 爬取http://example.com
python crawler.py http://example.com
```

## Options

```
可选参数：
  -h, --help             帮助显示此帮助消息并退出
  -t , --timeout         所有页面请求的超时时间，默认为5秒
  --cookie               设置http请求Cookie
  --proxy-server         设置爬虫的代理地址，爬虫会将所有请求转发至该服务端口
  --headless             浏览器的无头操作模式，默认为false
  --exclude-links        如果链接包含此关键字，则不会发出任何请求。多个关键字由字符“，”分隔
  --crawl-link-type      爬网程序爬网的网络资源类型，默认爬取xhr、fetch、document
  --crawl-external-links 设置是否爬取外部链接爬网，默认情况下，仅对同一网站链接进行爬网（不推荐）
```

## Examples

```bash
# 默认启动方式
python3 crawl.py http://example.com

# 以无头模式启动
python3 crawl.py http://example.com --headless

# 不爬取带有以下关键字的链接，支持正则表达式
python3 crawl.py http://example.com --exclude-links "logout|Logout"

# 设置Cookie，则爬虫所有的请求都会携带该Cookie
python3 crawl.py http://example.com --cookie "PHPSESSID=gbo3fci62fpig5vp4fq6a950h2; security=impossible"

# 设置代理
python3 crawl.py http://example.com --proxy-server "127.0.0.1:8000"
```

## Todo
- [ ] 性能优化，合理使用协程加快爬取速度并增加访问频率参数；
- [ ] 增加script（在考虑是否使用装饰器实现）加载模块，用于自定义操作，例如识别到用户登录界面，若有对应脚本可进行爆破，后期也可作网站指纹识别；
- [ ] 增加网站指纹识别功能;

