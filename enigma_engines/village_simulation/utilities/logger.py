import logging


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Setup a logger with the given name and level.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name. If it doesn't exist, create it.
    """
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        setup_logger(name)
    return logger


backend_logger = setup_logger("village_simulation.backend", logging.DEBUG)
