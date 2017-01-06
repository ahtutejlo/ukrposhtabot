import sqlite3
import logging


logger = logging.getLogger('UkrPoshtaBot')


class SQLighter:

    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()
        logger.debug('Connected to {}'.format(database))

    def get_all(self):
        with self.connection:
            logger.debug('Getting all rows.')
            return self.cursor.execute("""SELECT * FROM tracks""").fetchall()

    def check_if_exist(self, chat_id, track):
        """ Check if this user with this track number exist in db """
        with self.connection:
            rows = self.cursor.execute("""SELECT id FROM tracks WHERE chat_id = %s AND track = '%s';"""
                                       % (chat_id, track)).fetchall()
            return len(rows)

    def insert_new_track(self, chat_id, track, status, user_name, description):
        """ If there is no user with this track number - insert it """
        with self.connection:
            logger.debug('Checking if chat_id {} with track {} is present in db'.format(chat_id, track))
            rows = self.cursor.execute("""SELECT id FROM tracks WHERE chat_id = ? AND track = ?;""", (chat_id, track))\
                .fetchall()
            if len(rows) == 0:
                logger.debug('User with given track not found. Adding it...')
                query = "INSERT INTO tracks(chat_id, track, status, user_name, description) VALUES(?,?,?,?,?);"
                args = (chat_id, track, status, user_name, description)
                self.cursor.execute(query, args)
                self.connection.commit()
                logger.debug('User has been added.')
            else:
                logger.debug('User with given track number is found.')

    def update_status(self, status, chat_id, track):
        """ Update last status if it was has been changed """
        with self.connection:
            logger.debug('Updating status for track {} (chat_id {})'.format(track, chat_id))
            qry = '''UPDATE tracks SET status = ? WHERE chat_id = ? AND track = ?;'''
            self.cursor.execute(qry, (status, chat_id, track))
            self.connection.commit()

    def get_string(self, key, lang='uk'):
        """ Returns string with given key and lang. Default [uk]rainian """
        with self.connection:
            return str(self.cursor.execute("""SELECT ? FROM langs WHERE key = ?""", (key, lang)).fetchone()[0])

    def close(self):
        """ Close connection with db """
        self.connection.close()
        logger.debug('Connection closed')
