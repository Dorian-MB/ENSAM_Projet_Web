from flask import Flask, url_for, request, render_template, redirect
import sqlite3 as lite
import time
from pathlib import Path
import pandas as pd

main_path = Path(__file__).parent
BDD_PATH = str(main_path / "BDD.db")

def execute_sql(sql, parameters=(), bbd_path=BDD_PATH):
    con = lite.connect(bbd_path)
    con.row_factory = lite.Row
    cur = con.cursor()
    cur.execute(sql, parameters)
    table = cur.fetchall()
    con.close()
    return table


def commit_sql(sql, parameters=(), bbd_path=BDD_PATH):
    con = lite.connect(bbd_path)
    cur = con.cursor()
    cur.execute(sql, parameters)
    con.commit() # .commit() est utilisée pour appliquer les modifications apportées à la base de données
    con.close()


