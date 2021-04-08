# AUTOGENERATED! DO NOT EDIT! File to edit: 71_sqlite_repository.ipynb (unless otherwise specified).

__all__ = ['BaseRepository', 'InMemoryRepository', 'SqliteRepository']

# Cell

from typing import Any
from pydantic import BaseModel
from collections import defaultdict


class BaseRepository(BaseModel):
    session: Any = None

    def get_result(self, benchmark, result):
        pass

    def add_result(self, benchmark, result):
        pass


class InMemoryRepository(BaseRepository):
    results: dict = defaultdict(dict)

    def get_result(self, benchmark, result):
        return self.results.get(benchmark, {}).get(result, result)

    def add_result(self, benchmark, result):
        self.results[benchmark][result] = result

# Cell

import json
import sqlite3


class SqliteRepository(BaseRepository):
    connection: sqlite3.Connection

    class Config:
        arbitrary_types_allowed = True

    def execute_stmt(self, stmt, ignore_error=False):
        cursor = self.connection.cursor()
        try:
            cursor.execute(stmt)
        except sqlite3.OperationalError as exc:
            if not ignore_error:
                raise (exc)

    def create_benchmark_table(self):
        stmt = """
            create table benchmark (
                benchmark_id INTEGER PRIMARY KEY,
                created DATE DEFAULT (datetime('now','localtime')),
                machine_id TEXT NOT NULL UNIQUE,
                uname TEXT NOT NULL,
                data TEXT NOT NULL
            )
        """
        self.execute_stmt(stmt, ignore_error=True)

    def create_result_table(self):
        stmt = """
            create table result (
                result_id INTEGER PRIMARY KEY,
                benchmark_id integer not NULL,
                created DATE DEFAULT (datetime('now','localtime')),
                server text not NULL,
                client text not NULL,
                file_size integer not NULL,
                complete_size integer not NULL,
                elapsed real not NULL,
                FOREIGN KEY(benchmark_id) REFERENCES benchmark(benchmark_id)
            )
        """
        self.execute_stmt(stmt, ignore_error=True)

    def create_tables(self):
        self.create_benchmark_table()
        self.create_result_table()

    def add_benchmark(self, benchmark):
        stmt = """
            insert into benchmark (machine_id, uname, data)
            values (?, ?, ?)
        """
        cursor = self.connection.cursor()
        machine_id = benchmark.machine_id
        uname = benchmark.uname_json
        data = benchmark.json()
        try:
            cursor = cursor.execute(stmt, [machine_id, uname, data])
        except sqlite3.IntegrityError as e:
            pass
        self.connection.commit()

    def get_benchmark(self, benchmark):
        stmt = """
            select *
              from benchmark
             where machine_id=?
        """
        cursor = self.connection.cursor()
        cursor.execute(stmt, [benchmark.machine_id])
        return cursor.fetchone()

    def get_benchmark_id(self, benchmark):
        row = self.get_benchmark(benchmark)
        if row is None:
            return row
        return row[0]

    def get_result(self, benchmark, result):
        benchmark_id = self.get_benchmark_id(benchmark)
        if benchmark_id is None:
            self.add_benchmark(benchmark)
        benchmark_id = self.get_benchmark_id(benchmark)
        assert benchmark_id is not None
        stmt = """
            select *
              from result
             where benchmark_id=?
               and server=?
               and client=?
               and file_size=?
               and complete_size=?
        """
        cursor = self.connection.cursor()
        cursor.execute(
            stmt,
            [
                benchmark_id,
                result.server,
                result.client,
                result.file_size,
                result.complete_size,
            ],
        )
        row = cursor.fetchone()
        if row is None:
            return result
        result.elapsed = row[7]
        return result

    def add_result(self, benchmark, result):
        benchmark_id = self.get_benchmark_id(benchmark)
        columns = [
            "benchmark_id",
            "server",
            "client",
            "file_size",
            "complete_size",
            "elapsed",
        ]
        columns_str = ",".join(columns)
        values_str = ",".join(["?" for c in columns])
        stmt = f"""
            insert into result ({columns_str})
            values ({values_str})
        """
        cursor = self.connection.cursor()
        result_dict = result.dict()
        result_dict["benchmark_id"] = benchmark_id
        values = [result_dict[c] for c in columns]
        try:
            cursor = cursor.execute(stmt, values)
        except sqlite3.IntegrityError as e:
            pass
        self.connection.commit()

    @classmethod
    def build_repository(cls, database_name):
        conn = sqlite3.connect(database_name)
        repo = cls(connection=conn)
        repo.create_tables()
        return repo