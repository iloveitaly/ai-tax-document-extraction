# isort:skip_file
import logging
import typing as t

# root folder, like rails
from pathlib import Path

import structlog
from decouple import config


def is_testing():
    return environment == "test"


def is_production():
    return environment == "production"


def is_development():
    return environment == "development"


def griptape_logging_setup():
    from griptape.structures.structure import LOGGER_NAME

    griptape_logger = logging.getLogger("griptape")
    griptape_logger.setLevel(logging.DEBUG)


def openai_logging_setup():
    """
    Config below is subject to change

    https://stackoverflow.com/questions/76256249/logging-in-the-open-ai-python-library/78214464#78214464
    https://github.com/openai/openai-python/blob/de7c0e2d9375d042a42e3db6c17e5af9a5701a99/src/openai/_utils/_logs.py#L16
    https://www.python-httpx.org/logging/

    Related gist: https://gist.github.com/iloveitaly/aa616d08d582c20e717ecd047b1c8534
    """

    openai_log_path = root / "openai.log"
    openai_file_handler = logging.FileHandler(openai_log_path)

    openai_logger = logging.getLogger("openai")
    openai_logger.propagate = False
    openai_logger.handlers = []  # Remove all handlers
    openai_logger.addHandler(openai_file_handler)

    httpx_logger = logging.getLogger("httpx")
    httpx_logger.propagate = False
    httpx_logger.handlers = []  # Remove all handlers
    httpx_logger.addHandler(openai_file_handler)


def configure_logger():
    logger_factory = structlog.PrintLoggerFactory()

    # allow user to specify a log in case they want to do something meaningful with the stdout
    if python_log_path := config("PYTHON_LOG_PATH", default=None):
        python_log = open(
            python_log_path, "a", encoding="utf-8"
        )  # pylint: disable=consider-using-with
        logger_factory = structlog.PrintLoggerFactory(file=python_log)

    log_level = t.cast(str, config("LOG_LEVEL", default="WARN", cast=str))
    level = getattr(logging, log_level.upper())

    # TODO logging.root.manager.loggerDict
    # we need this option to be set for other non-structlog loggers
    logging.basicConfig(level=level)

    # TODO look into further customized format
    # https://cs.github.com/GeoscienceAustralia/digitalearthau/blob/4cf486eb2a93d7de23f86ce6de0c3af549fe42a9/digitalearthau/uiutil.py#L45

    structlog.configure(
        context_class=dict,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=logger_factory,
        cache_logger_on_first_use=True,
    )


def setup():
    if hasattr(setup, "complete") and setup.complete:
        return

    global environment, root, logger, log

    root = Path(__file__).parent.parent
    environment = t.cast(
        str, config("PYTHON_ENV", default="development", cast=str)
    ).lower()

    log = structlog.get_logger()

    # context manager to auto-clear context
    log.context = structlog.contextvars.bound_contextvars
    # clear thread-local context
    log.clear = structlog.contextvars.clear_contextvars
    # set thread-local context
    log.local = structlog.contextvars.bind_contextvars

    logger = log

    openai_logging_setup()
    configure_logger()

    if is_development():
        import pretty_traceback

        pretty_traceback.install()

    setup.complete = True


# side effects are bad, but it's fun to do bad things
setup()
