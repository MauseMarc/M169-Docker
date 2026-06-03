Hier ist die Datenbank
Im /Data liegen csv exports.
test.db ist die Datenbank datei mit allen Daten.
db_base.py existiert nur für die Verbindung zu der Datenbank. Hier nicht wichtig.
db_create.py ist der ursprüngliche Skript für die erstellung der Datenbank. Doch das brauchen wir auch nicht wenn wir direkt von der DB Datei exportieren.
csv_handler.py exportiert und importiert Daten von und zu csv Dateien.

Es gibt befehle um sqlite Datenbank zu sql skripts zu exportieren.
Dieses exportierte sql skript muss aber angepasst werden. Erstens die Datentypen sind anders.
Zweitens sind manche begriffe anders:
- AUTOINCREMENT -> AUTO_INCREMENT
etc.

Der Befehl zum exportieren:
    'sqlite3 test.db .dump > database_dump.sql'
