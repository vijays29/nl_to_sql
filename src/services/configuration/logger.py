import logging

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        
        formatter = logging.Formatter(
            fmt="[%(name)-25s]  %(asctime)s  |  %(levelname)-8s |  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
            )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    return logger
