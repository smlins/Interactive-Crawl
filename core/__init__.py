from core.crawl import crawl_task_run, MultiProcess, Pipe



def CrawlProcess(url, options, daemon=True):
    """
    Used to store the requested json data
    :param url:
    :param options:
    :param daemon:
    :return:
    """
    client_pipe, server_pipe = Pipe()
    process_task = MultiProcess(exec_func=crawl_task_run, func_args=(url, server_pipe, options), daemon=daemon)
    process_task.start()
    if client_pipe.recv() == 1:
        # process task stop
        process_task.state = 0

    return process_task

