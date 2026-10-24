
import os
import oracledb
from dotenv import load_dotenv

load_dotenv()

def conectar():
    dsn = oracledb.makedsn(
        os.getenv("ORACLE_HOST"),
        int(os.getenv("ORACLE_PORT", "1521")),
        sid=os.getenv("ORACLE_SID")
    )

    return oracledb.connect(
        user=os.getenv("ORACLE_USER"),
        password=os.getenv("ORACLE_PASSWORD"),
        dsn=dsn
    )
