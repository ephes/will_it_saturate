# AUTOGENERATED! DO NOT EDIT! File to edit: 71_sqlite_repository.ipynb (unless otherwise specified).

__all__ = ['BaseRepository', 'InMemoryRepository', 'dict_factory', 'SqliteRepository', 'BaseTable', 'HostTable',
           'ClientServerBase', 'ServerTable', 'ClientTable', 'ResultTable', 'register_default_tables']

# Cell

from typing import Any
from pydantic import BaseModel
from collections import defaultdict


class BaseRepository(BaseModel):
    session: Any = None

    def get_results(self):
        pass

    def add_result(self, result):
        pass


class InMemoryRepository(BaseRepository):
    results: dict = defaultdict(dict)

    def get_results(self):
        return self.results.get(benchmark, {}).get(result, result)

    def add_result(self, benchmark, result):
        self.results[benchmark][result] = result

# Cell

import json
import sqlite3

from pydantic import BaseModel


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class SqliteRepository(BaseRepository):
    connection: sqlite3.Connection
    tables: dict = {}

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def build_repository(cls, database_name):
        conn = sqlite3.connect(database_name)
        conn.row_factory = dict_factory
        repository = cls(connection=conn)
        return repository

    def create_tables(self):
        for name, table in self.tables.items():
            table.create_table()


class BaseTable(BaseModel):
    repository: BaseRepository

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repository.tables[self.table_name] = self

    @property
    def connection(self):
        return self.repository.connection

    def execute_stmt(self, stmt, ignore_error=False):
        cursor = self.connection.cursor()
        try:
            cursor.execute(stmt)
        except sqlite3.OperationalError as exc:
            if not ignore_error:
                raise (exc)

    def create_table(self):
        return self.execute_stmt(self.create_statement, ignore_error=True)

# Cell

from .hosts import HostDetails


class HostTable(BaseTable):
    table_name = "host"

    create_statement = f"""
        create table {table_name} (
            host_id INTEGER PRIMARY KEY,
            created DATE DEFAULT (datetime('now','localtime')),
            machine_id TEXT NOT NULL UNIQUE,
            details TEXT NOT NULL
        )
    """

    def get_machine_to_host_id(self, machine_ids):
        question_marks = ", ".join(["?" for _ in machine_ids])
        stmt = f"""
            select host_id, machine_id
              from {self.table_name}
             where machine_id in ({question_marks})
        """
        cursor = self.connection.cursor()
        cursor.execute(stmt, machine_ids)
        rows = cursor.fetchall()
        return {row["machine_id"]: row["host_id"] for row in rows}

    def insert_host_details(self, host_details):
        stmt = f"""
            insert into {self.table_name} (machine_id, details)
            values (?, ?)
        """
        cursor = self.connection.cursor()
        try:
            cursor = cursor.execute(
                stmt, [host_details.machine_id, host_details.json()]
            )
        except sqlite3.IntegrityError as e:
            pass
        self.connection.commit()
        return cursor.rowcount

    def get_or_create_hosts_from_result(self, result):
        machine_id_to_server_details = {
            result.server_details.machine_id: result.server_details,
            result.client_details.machine_id: result.client_details,
        }
        machine_ids = list(machine_id_to_server_details.keys())
        machine_to_host_id = self.get_machine_to_host_id(machine_ids)
        for machine_id, host_detail in machine_id_to_server_details.items():
            if machine_id not in machine_to_host_id:
                self.insert_host_details(host_detail)
        return self.get_machine_to_host_id(machine_ids)

    def get_all_host_id_to_host_details(self):
        stmt = f"""
            select *
              from {self.table_name}
        """
        cursor = self.connection.cursor()
        cursor.execute(stmt)
        rows = cursor.fetchall()

        # build host_id_to_host_details lookup
        host_id_to_host_details = {}
        for row in rows:
            kwargs = json.loads(row["details"])
            host_id_to_host_details[row["host_id"]] = HostDetails(**kwargs)
        return host_id_to_host_details

    def get_host_id_to_host_details(self, host_ids):
        host_id_to_host_details = self.get_all_host_id_to_host_details()
        return {
            host_id: host_id_to_host_details[host_id]
            for host_id in host_ids
            if host_id in host_id_to_host_details
        }

# Cell

from .registry import ModelParameters


class ClientServerBase(BaseTable):
    @property
    def create_statement(self):
        return f"""
            create table {self.table_name} (
                {self.table_name}_id INTEGER PRIMARY KEY,
                created DATE DEFAULT (datetime('now','localtime')),
                parameters TEXT NOT NULL UNIQUE
            )
        """

    @property
    def pk_name(self):
        return f"{self.table_name}_id"

    def fetch_all_rows(self):
        stmt = f"""
            select {self.pk_name}, parameters
              from {self.table_name}
        """
        cursor = self.connection.cursor()
        cursor.execute(stmt)
        return cursor.fetchall()

    def get_id_to_model(self):
        id_to_model = {}
        for row in self.fetch_all_rows():
            model_parameters = ModelParameters(**json.loads(row["parameters"]))
            id_to_model[row[self.pk_name]] = model_parameters.to_model()
        return id_to_model

    def get_model_to_id(self):
        model_to_id = {}
        for row in self.fetch_all_rows():
            model_to_id[row["parameters"]] = row[self.pk_name]
        return model_to_id

    def insert_model(self, model):
        stmt = f"""
            insert into {self.table_name} (parameters)
            values (?)
        """
        cursor = self.connection.cursor()
        parameters = json.dumps(model.params())
        try:
            cursor = cursor.execute(stmt, [parameters])
        except sqlite3.IntegrityError as e:
            pass
        self.connection.commit()
        return cursor.lastrowid

    def get_or_create_id(self, model):
        model_to_id = self.get_model_to_id()
        parameters_json = json.dumps(model.params())

        # insert model to database if it does not yet exist
        if parameters_json not in model_to_id:
            model_to_id[parameters_json] = self.insert_model(model)

        return model_to_id[parameters_json]


class ServerTable(ClientServerBase):
    table_name = "server"


class ClientTable(ClientServerBase):
    table_name = "client"

# Cell

from .results import Result


class ResultTable(BaseTable):
    table_name = "result"
    create_statement = f"""
        create table {table_name} (
            result_id INTEGER PRIMARY KEY,
            server_host_id integer not NULL,
            client_host_id integer not NULL,
            created DATE DEFAULT (datetime('now','localtime')),
            server_id integer not NULL,
            client_id integer not NULL,
            file_size integer not NULL,
            complete_size integer not NULL,
            elapsed real not NULL,
            FOREIGN KEY(server_host_id) REFERENCES host(host_id)
            FOREIGN KEY(client_host_id) REFERENCES host(host_id)
            FOREIGN KEY(server_id) REFERENCES server(server_id)
            FOREIGN KEY(client_id) REFERENCES client(client_id)
        )
    """

    @property
    def host(self):
        return self.repository.tables["host"]

    @property
    def server(self):
        return self.repository.tables["server"]

    @property
    def client(self):
        return self.repository.tables["client"]

    def add_result(self, result):
        machine_to_host_id = self.host.get_or_create_hosts_from_result(result)
        host_ids = {
            "server_host_id": machine_to_host_id[result.server_details.machine_id],
            "client_host_id": machine_to_host_id[result.client_details.machine_id],
        }

        server_and_client_ids = {
            "server_id": self.server.get_or_create_id(result.server),
            "client_id": self.client.get_or_create_id(result.client),
        }

        result_row = {
            **host_ids,
            **server_and_client_ids,
            "file_size": result.file_size,
            "complete_size": result.complete_size,
            "elapsed": result.elapsed,
        }
        columns = list(result_row.keys())
        columns_str = ",".join(columns)
        values_str = ",".join(["?" for c in columns])

        stmt = f"""
            insert into result ({columns_str})
            values ({values_str})
        """
        cursor = self.connection.cursor()

        values = [result_row[c] for c in columns]
        try:
            cursor = cursor.execute(stmt, values)
        except sqlite3.IntegrityError as e:
            pass
        self.connection.commit()
        return cursor.lastrowid

    def get_results(self):
        # fetch all host details from DB
        host_id_to_host_details = self.host.get_all_host_id_to_host_details()

        # fetch all client/server parameters from DB
        server_id_to_model = self.server.get_id_to_model()
        client_id_to_model = self.client.get_id_to_model()

        # fetch all result rows from DB
        stmt = """
            select *
              from result
        """
        cursor = self.connection.cursor()
        cursor.execute(stmt)
        rows = cursor.fetchall()

        # build results
        results = []
        for row in rows:
            client_host_details = host_id_to_host_details[row["client_host_id"]]
            server_host_details = host_id_to_host_details[row["server_host_id"]]
            server = server_id_to_model[row["server_id"]]
            client = client_id_to_model[row["client_id"]]
            kwargs = {
                **row,
                "server": server,
                "client": client,
                "server_details": server_host_details,
                "client_details": client_host_details,
            }
            results.append(Result(**kwargs))
        return results


def register_default_tables(repository):
    results = ResultTable(repository=repository)
    hosts = HostTable(repository=repository)
    servers = ServerTable(repository=repository)
    clients = ClientTable(repository=repository)
    repository.create_tables()