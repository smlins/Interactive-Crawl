import asyncio
from time import sleep
from common.logger import logging
from pyppeteer.page import Page


class PageManage:
    def __init__(self):
        self.page_list = []


    def push(self, page: Page):
        self.page_list.append(page)

    def pop(self):
        if self.empty():
            return None

        return self.page_list.pop(0)

    def multi_push(self, pages: list):
        self.page_list += pages

    def empty(self):
        if len(self.page_list) == 0:
            return True
        else:
            return False

    def pages(self):
        return self.page_list
