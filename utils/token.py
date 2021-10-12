"""GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

Copyright (c) 2021 gunyu1019

PUBG BOT is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

PUBG BOT is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with PUBG BOT.  If not, see <http://www.gnu.org/licenses/>.
"""

import pymysql.cursors

from config.config import parser
from utils.database import get_database

connect = get_database()

cur = connect.cursor(pymysql.cursors.DictCursor)
try:
    cur.execute("SELECT token from Music_Bots")
except pymysql.err.DatabaseError:
    client_list = {
        "token": parser.get("DEFAULT", "token"),
    }
else:
    client_list = cur.fetchone()

token = client_list.get('token')
connect.close()
