from typing import Dict, Optional

from dbtypes import SimulationData


class DBConnection:
    from typing import Any

    def __init__(self, host: str, port: int, db_name: str, user: str, password: str):
        self._host = host
        self._port = port
        self._db_name = db_name
        self._user = user
        self._password = password

    def _run_query(self, query: str, args: Dict[str, Any] = None) -> Optional[Any]:
        from pg8000 import connect
        from common import eprint
        import pg8000
        pg8000.paramstyle = "named"
        try:
            with connect(host=self._host, port=self._port, database=self._db_name, user=self._user,
                            password=self._password) as connection:
                connection.autocommit = True
                with connection.cursor() as cursor:
                    return cursor.execute(query, args)
        except Exception as ex:
            eprint("The query \"" + query + "\" failed with " + str(ex))
            return None

    def store_data(self, data: SimulationData) -> Any:
        from lxml.etree import tostring
        from aiExchangeMessages_pb2 import TestResult
        result = data.simulation_task.get_state()
        if result is TestResult.Result.SUCCEEDED:
            successful = "TRUE"
        elif result is TestResult.Result.FAILED:
            successful = "FALSE"
        elif result is TestResult.Result.SKIPPED:
            successful = "NULL"
        else:
            raise ValueError("SimulationData can not be stored (data.simulation_task.state() = " + str(result) + ").")
        args = {
            "environment": tostring(data.environment.getroot()),
            "criteria": tostring(data.criteria),
            "successful": successful,
            "started": data.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "finished": data.end_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self._run_query("""
        INSERT INTO tests VALUES
            (DEFAULT, :environment, :criteria, :successful, :started, :finished)
        """, args)
        print(id)
        return None
