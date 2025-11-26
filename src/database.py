# Re-export from new location for backward compatibility
from src.infrastructure.db.connection import (
    create_pool,
    close_pool,
    get_pool,
    get_db_pool,
    get_db_connection,
    check_pool_health,
    DEFAULT_MIN_SIZE,
    DEFAULT_MAX_SIZE,
    DEFAULT_MAX_QUERIES,
    DEFAULT_MAX_INACTIVE_CONNECTION_LIFETIME,
    DEFAULT_COMMAND_TIMEOUT,
    DEFAULT_CONNECT_TIMEOUT,
)
