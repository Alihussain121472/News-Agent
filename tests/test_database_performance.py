import os
import unittest
from unittest.mock import patch

import database


class DatabaseInitializationTests(unittest.TestCase):
    def test_schema_initialization_runs_once_per_process(self):
        database_key = 'postgresql://test/schema-init-guard'
        database._initialized_databases.discard(database_key)
        try:
            with patch.dict(os.environ, {'DATABASE_URL': database_key}, clear=False), \
                    patch.object(database.NewsDatabase, 'init_database') as initialize:
                database.NewsDatabase()
                database.NewsDatabase()

            initialize.assert_called_once_with()
        finally:
            database._initialized_databases.discard(database_key)


if __name__ == '__main__':
    unittest.main()
