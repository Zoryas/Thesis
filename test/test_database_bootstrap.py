import importlib
import sys
import unittest
from unittest import mock

import mysql.connector


class DatabaseBootstrapTests(unittest.TestCase):
    def test_init_database_handles_missing_database_configuration(self):
        with mock.patch("mysql.connector.connect", side_effect=mysql.connector.errors.DatabaseError("boom")):
            sys.modules.pop("app", None)
            app = importlib.import_module("app")
            self.assertFalse(getattr(app, "DB_READY", False))


if __name__ == "__main__":
    unittest.main()
