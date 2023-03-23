import asyncio
import re
from time import sleep
from common.encrypt import md5, random_str
from common.urlparse import UrlParse
from common.logger import logging
import pyppeteer
from pyppeteer import launch
from pyppeteer.page import Page
from pyppeteer.worker import Worker
from pyppeteer.network_manager import Response, Request


class Browsers:
    def __init__(self, max_page_nums=1, timeout=3, http_context_callback=None, filter_req_type=None, headless=False,
                 args=None, loop=None, headers=None, screen_size=None, exclude_links_keyword=None):
        if args is None:
            args = []
        default_args = ['--start-maximized', '--enable-automation', '--no-sandbox', '--disable-infobars',
                        '--disable-gpu']
        args += default_args

        if filter_req_type is None:
            filter_req_type = ['xhr', 'document', 'fetch']

        self.browser = None
        self.context = None
        self.page = None
        self.headers = headers
        self.page_list = []
        self.timeout = timeout
        self.exclude_links_keyword = exclude_links_keyword
        self.filter_req_type = filter_req_type
        self.max_page_nums = max_page_nums
        self.options = {
            'headless': headless,
            'ignorehttpserrrors': True,
            'args': args,
            'handleSIGINT': False,
            'handleSIGTERM': False,
            'handleSIGHUP': False
        }
        self.http_context_callback = http_context_callback
        self.is_init = False
        self.loop = loop if loop else asyncio.new_event_loop()
        self.screen_size = screen_size
        self.accessed_link = {}
        self.exclude_content = []
        self._onclick_events = []
        self._form_records = []

    @classmethod
    def get_unique_url_key(cls, url, slat='', whole=False):
        """
        to be optimized
        :param slat:
        :param url:
        :return:
        """
        try:
            if not whole:
                url_obj = UrlParse(url)
                padding = '{}{}{}'.format(
                    url_obj.geturl(only_domain=True), url_obj.path,
                    ''.join(list(set(url_obj.resolve_params(url_obj.query)))) if url_obj.query else '')
            else:
                padding = url
        except TypeError as e:
            padding = url
        key = md5(padding + slat)
        return key

    async def init_browser(self):
        """
        Initialize browser and page
        :return:
        """
        # 有一个Error待记录
        self.browser = await launch(**self.options)
        self.context = self.browser.browserContexts[0]
        self.page_list = await self.context.pages()
        self.page = self.page_list[0]


    async def init_page(self, page: Page = None):
        page = page if page else self.page
        if self.headers:
            await page.setExtraHTTPHeaders(self.headers)
        if self.screen_size:
            await page.setViewport(self.screen_size)
        page.setDefaultNavigationTimeout(self.timeout * 1000)
        # await page.setRequestInterception(True)
        await page.setUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/66.0.3359.181 Safari/537.36")
        # page.on('request', lambda request: asyncio.ensure_future(self.intercept_request(request)))
        page.on('response', lambda response: asyncio.ensure_future(self.intercept_response(response)))
        page.on('dialog', lambda dialog: asyncio.ensure_future(self.close_dialog(dialog)))

    @classmethod
    async def close_dialog(cls, dialog):
        await dialog.dismiss()

    async def intercept_request(self, request: Request):
        try:
            if request.resourceType in self.filter_req_type:
                u_obj = UrlParse(request.url)
                key = self.get_unique_url_key(url=u_obj.geturl(only_domain=True), slat=u_obj.params)
                req_json = {'url': request.url, 'method': request.method,
                            'data': request.postData if request.postData else '',
                            # 'headers': request.headers
                            }

                if key not in self.accessed_link:
                    self.accessed_link[key] = request.url
                if key in self.accessed_link:
                    # print(req_json['method'], req_json['url'], req_json['data'])
                    if self.http_context_callback:
                        self.http_context_callback(req_json, {})
        except Exception as e:
            logging.error(e, exc_info=True)
        finally:
            await request.continue_()

    async def intercept_response(self, response: Response):
        request = response.request
        if request.resourceType in self.filter_req_type:
            req_json = {
                'url': request.url,
                'method': request.method,
                'data': request.postData if request.postData else '',
                'headers': request.headers
            }
            res_json = {
                'status': response.status,
                'headers': response.headers,
                'body': ''
            }
            if res_json['status'] == '200':
                body = await response.text()
                res_json['body'] = body if body else ''
            # print(res_json['status'], req_json['method'], req_json['url'], req_json['data'])
            if self.http_context_callback:
                self.http_context_callback(request=req_json, response=res_json)


    async def waitEventsForNavigation(self, page: Page, event):
        try:
            await asyncio.wait({
                asyncio.create_task(event),
                asyncio.create_task(page.waitForNavigation())
            })
        except BaseException as e:
            logging.error(e, exc_info=True)


    async def waitEventsForResponse(self, page: Page, event):
        try:
            await asyncio.wait({
                asyncio.create_task(event),
                asyncio.create_task(
                    page.waitForResponse(lambda res: res.request.resourceType in ['xhr', 'document', 'fetch']))
            })
        except pyppeteer.errors.TimeoutError as e:
            logging.error('{} for {}'.format(e, page.url))

    def filter_keyword(self, content):
        if self.exclude_links_keyword:
            if content in self.exclude_content:
                return False
            elif re.search(self.exclude_links_keyword, content):
                self.exclude_content.append(content)
                return False

        return True

    def filter_links(self, urls: list):
        result = []
        for u in urls:
            try:
                u_obj = UrlParse(u)
                key = self.get_unique_url_key(url='{}{}'.format(u_obj.geturl(only_domain=True), u_obj.path),
                                              slat=u_obj.params)
                if key not in self.accessed_link:
                    result.append(u)
            except TypeError as e:
                logging.error(e, exc_info=True)

        return result

    async def _get_onclick(self, page: Page, content=None, callback=None):
        content = content if content else await page.content()
        onclick_events = await page.querySelectorAll('*[onclick]')
        onclick_events_attrs = re.findall('onclick=\"(.+?)\"', content)
        for i in range(len(onclick_events_attrs)):
            if not self.filter_keyword(onclick_events_attrs[i]):
                continue

            onclick_events = await page.querySelectorAll('*[onclick]')
            if not onclick_events_attrs and not onclick_events:
                await self.waitEventsForNavigation(page, page.goBack())
                onclick_events = await page.querySelectorAll('*[onclick]')
                if not onclick_events:
                    break

            key = self.get_unique_url_key(onclick_events_attrs[i], whole=True)
            if key in self._onclick_events:
                continue

            self._onclick_events.append(key)
            try:
                if 'window.open' in onclick_events_attrs[i]:
                    await onclick_events[i].click()
                    await asyncio.sleep(0.5)
                    page_list = await self.context.pages()
                    offset = page_list.index(page)
                    if len(page_list) >= 2:
                        new_window = page_list[offset + 1]
                        await self.init_page(new_window)
                        await self.trigger_events(new_window, callback=callback)
                        await asyncio.sleep(0.5)
                        await new_window.close()
                elif 'window.location' in onclick_events_attrs[i]:
                    await self.waitEventsForNavigation(page, onclick_events[i].click())
                    await self.trigger_events(page, callback=callback)
            except BaseException as e:
                logging.error(e, exc_info=True)


        return page

    async def _get_href(self, page: Page, callback=None):
        urls = []
        links = await page.querySelectorAllEval('a', 'elements => elements.map(elem => elem.href)')
        links_labels = await page.querySelectorAll('a')
        for i in range(len(links)):
            if not self.filter_keyword(links[i]):
                continue
            if links[i].startswith('http'):
                urls.append(links[i])
            elif links[i].startswith('javascript:') \
                    and not (links[i].endswith('script:;') or links[i].endswith('void(0);')):
                try:
                    links_labels = await page.querySelectorAll('a')
                    if not links_labels:
                        logging.error('The page was also updated, but was not retrieved')
                        break
                    await self._easy_click(page=page, click_event=links_labels[i].click, new_open=False)
                except BaseException as e:
                    logging.error(e, exc_info=True)

        urls = self.filter_links(urls)
        # print(urls)
        if callback:
            callback(urls)

        return page

    async def _get_form(self, page: Page, callback=None):
        form_tables_info = await page.querySelectorAllEval(
            'form',
            'elements => elements.map(elem => { return {method: elem.method, name: elem.name, action: elem.action}})'
        )
        forms_tables = await page.querySelectorAll('form')

        is_retry = True

        for offset in range(len(forms_tables)):
            if is_retry:
                forms_tables = await page.querySelectorAll('form')
                is_retry = False
                if not form_tables_info and not forms_tables:
                    logging.error('The page was also updated, but was not retrieved, exit')
                    break
            key = self.get_unique_url_key(form_tables_info[offset]['action'],
                                          slat=str(form_tables_info[offset]['name']), whole=True)
            if key in self._form_records:
                continue
            self._form_records.append(key)
            input_labels = await forms_tables[offset].querySelectorAll('input')
            input_labels += await forms_tables[offset].querySelectorAll('textarea')
            input_labels_info = await forms_tables[offset].querySelectorAllEval('input',
                                                                                '(els) => els.map(el => {return {'
                                                                                'type: el.type, name: el.name, '
                                                                                'value: el.value}})')
            input_labels_info += await forms_tables[offset].querySelectorAllEval('textarea',
                                                                                 '(els) => els.map(el => {return {'
                                                                                 'type: el.type, name: el.name, '
                                                                                 'value: el.value}})')
            submit_button = None

            for i in range(len(input_labels_info)):
                if input_labels_info[i]['type'] in ['text', 'password', 'textarea']:
                    await input_labels[i].type(random_str())
                elif input_labels_info[i]['type'] == 'submit':
                    submit_button = input_labels[i]

            # form 表单submit都需要在当前页面打开
            if submit_button:
                await self._easy_click(page=page, click_event=submit_button.click, new_open=False)
                is_retry = True
                # await page.waitForNavigation()
                await asyncio.sleep(2)
                await self.trigger_events(page, callback=callback)
                await self.waitEventsForNavigation(page, page.goBack())

        return page

    async def _easy_click(self, page: Page, click_event, new_open=False):
        try:
            if new_open:
                await page.keyboard.down('Control')
                await click_event()
                await page.keyboard.up('Control')
            else:
                await self.waitEventsForNavigation(page=page, event=click_event())
        except BaseException as e:
            logging.error(e, exc_info=True)

    async def trigger_events(self, page: Page, callback=None):
        try:
            page = await self._get_href(page, callback=callback)
            page = await self._get_onclick(page, callback=callback)
            page = await self._get_form(page, callback=callback)
        except Exception as e:
            logging.error(e, exc_info=True)

        return page

    async def go_by_page(self, url, callback=None):
        """
        Access the specified url by the page and trigger the following events:
            1. If there is an input box, enter random characters
            2. Click the button if it exists
            3. Get all urls on the page
        :param url:
        :param callback:
        :return:
        """

        key = self.get_unique_url_key(url)
        if key in self.accessed_link:
            raise

        if not self.is_init:
            await self.init_browser()
            await self.init_page()
            self.is_init = True

        while not self.page_list:
            logging.info('wait for idle page')
            sleep(1)

        page: Page = self.page_list.pop(0)

        try:
            await page.goto(url=url)
            await asyncio.sleep(1)
            await self.trigger_events(page, callback)
        except pyppeteer.errors.TimeoutError as e:
            logging.error('{} for {}'.format(e, page.url))
        except BaseException as e:
            logging.error('{} for {}'.format(e, page.url))
        finally:
            self.page_list.append(page)

    async def _close(self):
        logging.info('page will be closed')
        for page in self.page_list:
            await page.close()
        logging.info('browser will be closed')
        await self.browser.close()

    def close(self):
        task = asyncio.run_coroutine_threadsafe(self._close(), self.loop)
        while not task.done():
            logging.info('Wait for the completion of the coordination task')
            sleep(1)


async def main(url):
    a = Browsers(timeout=5)

    await a.go_by_page(url)
    await asyncio.sleep(3)


def test(loop, context):
    print(context['exception'])


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(test)
    loop.run_until_complete(main('http://47.112.153.42:8082'))

