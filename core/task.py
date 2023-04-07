import asyncio
from time import sleep
from multiprocessing import Process, Pipe
from core.base import CDict
from common.logger import logging
import threading


class MultiCoroutine:
    def __init__(self, loop, concurrency=10, *args, **kwargs):
        """
            multiple coroutine task manager
        """
        self.tasks = CDict()
        self.state = 'run'
        self.semaphore = asyncio.Semaphore(concurrency)
        # gain new event loop of current process
        self.loop = loop

        self.loop.set_exception_handler(self.handle_loop_exception)

    def __getitem__(self, item):
        """
        rewrite __getitem__ in order to find the task id easily
        :param item:
        :return:
        """
        try:
            return self.tasks[item]
        except KeyError:
            raise RuntimeError('task {} not exist!'.format(item))

    def handle_loop_exception(self, loop, context):
        """
        :param loop:
        :param context:
            {'message': '', 'exception': '', 'future': ''}
        :return:
        """
        logging.error(context['exception'])

    async def sem_task(self, coroutine):
        """
        control the number of coroutine
        :param coroutine:
        :return:
        """
        async with self.semaphore:
            return await coroutine


    def add_task(self, coroutine):
        """
        add coroutine task
        :param coroutine:
        :return:
        """
        if self.loop is None:
            raise RuntimeError('event loop not create!')

        # Automatically name tasks
        task_id = 'Task-{}'.format(len(self.tasks.ret_keys()))

        # 有一个Error待记录
        task = asyncio.run_coroutine_threadsafe(self.sem_task(coroutine), loop=self.loop)

        # Send signals to synchronize tasks
        self.loop._csock.send(b'\0')
        # name = task.get_name()
        self.tasks[task_id] = task
        return task_id

    def stop_task(self, name, nowait=False):
        self[name].cancel()
        if not nowait:
            while not self.tasks[name].cancelled():
                sleep(0.5)

    @classmethod
    def start_loop(cls, loop):
        try:
            asyncio.set_event_loop(loop)
            loop.run_forever()
        except Exception as e:
            logging.error(e, exc_info=True)
        finally:
            logging.info('loop will be close.')
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

    def run(self) -> None:
        # asyncio.set_event_loop(self.loop)
        task = threading.Thread(target=self.start_loop, args=(self.loop,), daemon=True)
        task.start()

    def is_done(self, name):
        if name:
            return self[name].done()
        else:
            raise NameError

    def stop_running(self):
        asyncio.set_event_loop(self.loop)
        self.loop.stop()
        logging.info('loop will be stopped')

    def is_finish(self):
        """
        判断当前协程任务是否都完成
        :return:
        """
        finish = True
        for task_id in self.tasks.generator():
            if not self.is_done(task_id):
                finish = False
                break
        return finish


class MultiProcess(Process):
    def __init__(self, exec_func, func_args: tuple = (), callback_after_completion=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = 1  # stop is 0, running is 1, finish is 2
        self.exec_func = exec_func
        self.func_args = func_args
        self._result = None
        self.callback_after_completion = callback_after_completion

    def run(self):
        while True:
            if self.state == 1:
                try:
                    self._result = self.exec_func(*self.func_args)
                    self.finished()
                except BaseException as e:
                    logging.error(e, exc_info=True)
            elif self.state == 2:
                # The task will not end after completion, but will be suspended
                sleep(1)
            else:
                break

    def finished(self):
        self.state = 2
        if self.callback_after_completion:
            self.callback_after_completion(self._result)

    def get_result(self):
        if self.state != 2:
            return False
        return self._result
