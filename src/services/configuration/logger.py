import logging

def get_logger(name: str) -> logging.Logger:
    """
    Initializes and returns a logger instance with a specified name.

    This function sets up a stream handler with a custom formatter,
    applies INFO-level logging, and ensures that multiple handlers
    are not added if the logger is already initialized.

    Args:
        name (str): The name of the logger (typically the module or component name).

    Returns:
        logging.Logger: Configured logger instance ready for use.
    """
    logger = logging.getLogger(name)

    # Only add handler if none exist to prevent duplicate logging
    if not logger.hasHandlers():
        handler = logging.StreamHandler()  # Sends log output to standard output (console)

        # Define the log message format including timestamp, level, and custom name
        formatter = logging.Formatter(
            fmt="[%(name)-25s]  %(asctime)s  |  %(levelname)-8s |  %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)     # Apply the formatter to the handler
        logger.addHandler(handler)          # Attach the handler to the logger

        logger.setLevel(logging.INFO)       # Set the default logging level to INFO
        logger.propagate = False            # Prevent logs from being passed to the root logger

    return logger
