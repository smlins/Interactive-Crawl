import asyncio
import time
from common.logger import logging
from common.urlparse import UrlParse
from script import script_hook
from core.browser import Browsers
from core.task import MultiCoroutine, MultiProcess, Pipe


class Crawl:
    def __init__(self, url, maximum_requests=1, loop=None, external_links=False, timeout=3, **kwargs):
        self.url = url
        self.url_obj = UrlParse(url)
        self.external_links = external_links
        self.not_accessed_dict = {}
        self.accessed_dict = {}  # Used to store the requested json data
        self.all_access = {}  # Used to store all requested urls
        self.maximum_requests = maximum_requests
        self.loop = loop if loop else asyncio.get_event_loop()
        self.browser_handle = Browsers(
            max_page_nums=self.maximum_requests,
            http_context_callback=self.http_context_handle,
            headless=kwargs['headless'] if 'headless' in kwargs else False,
            args=kwargs['args'] if 'args' in kwargs else None,
            loop=self.loop,
            filter_req_type=kwargs['filter_req_type'] if 'filter_req_type' in kwargs else None,
            timeout=timeout,
            headers=kwargs['headers'] if 'headers' in kwargs else None,
            screen_size=kwargs['screen_size'] if 'screen_size' in kwargs else None,
            exclude_links_keyword=kwargs['exclude_links'] if 'exclude_links' in kwargs else None,
            prohibit_load=kwargs['prohibit_load'] if 'prohibit_load' in kwargs else None,
            intercept_request=kwargs['intercept_request'] if 'intercept_request' in kwargs else None,
        )
        self.state = 1  # stop is 0, running is 1, finish is 2
        self.thread_task = MultiCoroutine(concurrency=maximum_requests, daemon=False, loop=self.loop)

    def handle_link(self, url, is_accessed=False, **kwargs):
        """
        type of url is list if called by go_by_page, type of url is str if called by http_context_handle
        to be optimized
        :param is_accessed:
        :param url: list ot str
        :return:
        """

        urls = [url] if isinstance(url, str) else url
        is_echo = False
        if is_accessed:
            for url in urls:
                u_obj = UrlParse(url)
                key = self.browser_handle.get_unique_url_key(
                    url='{}{}'.format(u_obj.geturl(only_domain=True), u_obj.path), slat=u_obj.query)
                # Delete if it already exists in the unreachable dict
                if key in self.not_accessed_dict:
                    self.not_accessed_dict.pop(key)

                # Append if it does not exist in the visited dict
                if key not in self.accessed_dict:
                    self.accessed_dict[key] = kwargs
                    is_echo = True
                    # self.all_access[key] = url
                elif self.accessed_dict[key]['request']['data'] == '' and kwargs['request']['data'] != '':
                    self.accessed_dict[key] = kwargs
                    is_echo = True
            return is_echo


        else:
            for url in urls:
                u_obj = UrlParse(url)
                key = self.browser_handle.get_unique_url_key(
                    url='{}{}'.format(u_obj.geturl(only_domain=True), u_obj.path), slat=u_obj.params)
                # Append if it already exists in the unreachable list and visited dict
                if key not in self.not_accessed_dict and key not in self.accessed_dict and key not in self.all_access:
                    if url.startswith(self.url_obj.geturl(only_domain=True)):
                        self.not_accessed_dict[key] = url
                    elif self.external_links:
                        self.not_accessed_dict[key] = url

    @script_hook
    def http_context_handle(self, request, response):
        """
        Callback function for http request interception
        :param request: Json data like format {
                'url': url,
                'method': method,
                'postData': data,
                'headers': headers
        }
        :param response: Json data like format {
                'status': status,
                'headers': headers,
                'body': ''  # Don't save the data temporarily
        }
        :return:
        """
        is_echo = self.handle_link(request['url'], is_accessed=True, request=request)
        sign = '[+]'
        if is_echo:
            logging.info(
                '{} {} {} {} {}'.format(sign, response['status'], request['method'], request['url'], request['data']))

    def init_crawl(self):
        self.handle_link(self.url)

    def start_crawl(self):
        self.init_crawl()
        self.thread_task.run()
        while self.not_accessed_dict or not self.thread_task.is_finish():
            try:
                if self.not_accessed_dict and self.thread_task.is_finish():
                    key = list(self.not_accessed_dict.keys())[0]
                    url = self.not_accessed_dict.pop(key)
                    self.all_access[key] = url
                    if key in self.accessed_dict:
                        logging.info('pass {}'.format(url))
                        continue
                    # logging.info('add link task: {}'.format(url))
                    self.thread_task.add_task(coroutine=self.browser_handle.go_by_page(url, callback=self.handle_link))
                else:
                    time.sleep(1)
            except BaseException as e:
                logging.error(e, exc_info=True)

    def stop_crawl(self):
        self.state = 2
        self.browser_handle.close()
        self.thread_task.stop_running()
        # self.browser_handle.destroy()

    def output_json(self):
        json_data = []
        for key in self.accessed_dict:
            # print(self.accessed_dict[key]['request'])
            json_data.append(self.accessed_dict[key]['request'])
        logging.info('A total of {} crawling links'.format(len(json_data)))
        return json_data


def crawl_task_run(url, server_pipe, options=None, maximum_requests=1):
    """
    Entry function of crawler
    :param options:
    :param url:
    :param server_pipe: Used to transmit the completion signal to the main process
    :param maximum_requests: maximum coroutine
    :return:
    """
    # args = options['args']
    # headless = options['headless']
    # req_type = options['req_type']
    # external_links = options['external_links']
    # timeout = options['timeout']
    # headers = options['headers']
    # screen_size = options['screen_size']
    # prohibit_load = options['prohibit_load']
    # exclude_links = options['exclude_links']
    # interception_request = options['interception_request']
    task = Crawl(
        url=url,
        maximum_requests=maximum_requests,
        **options
    )
    task.start_crawl()
    logging.info('thread task is exit')
    task.output_json()
    task.stop_crawl()
    # Send completion signal through the server pipeline
    server_pipe.send(2)
