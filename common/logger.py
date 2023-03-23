import logging
import colorlog


class Log:
    def __init__(self, name=None, log_level=logging.DEBUG):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)

        console_fmt = '%(log_color)s%(asctime)s - %(levelname)s - %(module)s[line:%(lineno)d] - %(message)s'

        color_config = {
            'DEBUG': 'cyan',
            'INFO': 'light_green',
            'WARNING': 'light_yellow',
            'ERROR': 'light_red',
            'CRITICAL': 'purple',
        }

        console_formatter = colorlog.ColoredFormatter(fmt=console_fmt, log_colors=color_config)

        console_handler = logging.StreamHandler()

        console_handler.setFormatter(console_formatter)


        if not self.logger.handlers:
            self.logger.addHandler(console_handler)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message, exc_info=False):
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message):
        self.logger.critical(message)


logging = Log(log_level=logging.INFO)