import structlog
import logging
import better_exceptions
from sqlalchemy import create_engine, text


better_exceptions.MAX_LENGTH = None

# Configure structlog to use colorized output for the terminal
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer(colors=True, sort_keys=True),
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    cache_logger_on_first_use=True,
)

# Disable colorized output for the text logs
logging.basicConfig(level=logging.INFO, format="%(message)s")

logger = structlog.get_logger()


if __name__ == "__main__":
    logger.info("Logging configured successfully.")
