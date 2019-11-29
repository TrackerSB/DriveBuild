from typing import Dict, Optional
from logging import getLogger

_logger = getLogger("DriveBuild.Client.DBHandler")


class DBConnection:
    from typing import Any

    def __init__(self, host: str, port: int, db_name: str, user: str, password: str):
        self._host = host
        self._port = port
        self._db_name = db_name
        self._user = user
        self._password = password

    def run_query(self, query: str, args: Dict[str, Any] = None) -> Optional[Any]:
        from pg8000 import connect
        import pg8000
        pg8000.paramstyle = "named"
        try:
            with connect(host=self._host, port=self._port, database=self._db_name, user=self._user,
                            password=self._password) as connection:
                connection.autocommit = True
                with connection.cursor() as cursor:
                    return cursor.execute(query, args)
        except Exception:
            _logger.exception("The query \"" + query + "\" failed")
            return None
