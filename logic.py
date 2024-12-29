import sqlite3
from config import DATABASE

groups = [ (_,) for _ in ([])]
statuses = [ (_,) for _ in (['Постоянное расписание', 'Замены', 'Изменённое расписание', 'Особый день', 'Экзамен'])]

class DB_Manager:
    def __init__(self, database):
        self.database = database
        
    def create_tables(self):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.execute('''CREATE TABLE schedules (
                            schedule_id INTEGER PRIMARY KEY,
                            schedule_name TEXT NOT NULL,
                            description TEXT,
                            image IMG,
                            status_id INTEGER,
                            FOREIGN KEY(status_id) REFERENCES status(status_id)
                        )''') 
            conn.execute('''CREATE TABLE group (
                            group_id INTEGER PRIMARY KEY,
                            group_name TEXT
                        )''')
            conn.execute('''CREATE TABLE schedule_groups (
                            schedule_id INTEGER,
                            group_id INTEGER,
                            FOREIGN KEY(schedule_id) REFERENCES schedules(schedule_id),
                            FOREIGN KEY(group_id) REFERENCES groups(group_id)
                        )''')
            conn.execute('''CREATE TABLE status (
                            status_id INTEGER PRIMARY KEY,
                            status_name TEXT
                        )''')
            conn.commit()

    def __executemany(self, sql, data):
        conn = sqlite3.connect(self.database)
        with conn:
            conn.executemany(sql, data)
            conn.commit()
    
    def __select_data(self, sql, data = tuple()):
        conn = sqlite3.connect(self.database)
        with conn:
            cur = conn.cursor()
            cur.execute(sql, data)
            return cur.fetchall()
        
    def default_insert(self):
        sql = 'INSERT OR IGNORE INTO groups (group_name) values(?)'
        data = groups
        self.__executemany(sql, data)
        sql = 'INSERT OR IGNORE INTO status (status_name) values(?)'
        data = statuses
        self.__executemany(sql, data)


    def insert_schedule(self, data):
        sql = """INSERT INTO schedules (user_id, schedule_name, url, status_id) values(?, ?, ?, ?)""" 
        self.__executemany(sql, [data])


    def insert_group(self, schedule_name, group):
        sql = 'SELECT schedule_id FROM schedules WHERE schedule_name = ? AND user_id = ?'
        schedule_id = self.__select_data(sql, (schedule_name))[0]
        group_id = self.__select_data('SELECT group_id FROM groups WHERE group_name = ?', (group,))[0][0]
        data = [(schedule_id, group_id)]
        sql = 'INSERT OR IGNORE INTO schedule_groups VALUES(?, ?)'
        self.__executemany(sql, data)


    def get_statuses(self):
        sql = "SELECT status_name from status" 
        return self.__select_data(sql)
        

    def get_status_id(self, status_name):
        sql = 'SELECT status_id FROM status WHERE status_name = ?'
        res = self.__select_data(sql, (status_name,))
        if res: return res[0][0]
        else: return None

    def get_schedules(self):
        sql = """SELECT * FROM schedules""" 
        return self.__select_data(sql)
        
    def get_schedule_id(self, schedule_name):
        return self.__select_data(sql='SELECT schedule_id FROM schedules WHERE schedule_name = ?', data = (schedule_name))[0]
        
    def get_groups(self):
        return self.__select_data(sql='SELECT * FROM groups')
    
    def get_schedule_groups(self, schedule_name):
        res = self.__select_data(sql='''SELECT group_name FROM schedules 
                                        JOIN schedule_groups ON schedules.schedule_id = schedule_groups.schedule_id 
                                        JOIN groups ON groups.group_id = schedule_groups.group_id 
                                        WHERE schedule_name = ?''', data = (schedule_name,) )
        return ', '.join([x[0] for x in res])
    
    def get_schedule_info(self, schedule_name):
        sql = """
                                        SELECT schedule_name, description, url, status_name FROM schedules 
                                        JOIN status ON
                                        status.status_id = schedules.status_id
                                        WHERE schedule_name=?
                                        """
        return self.__select_data(sql=sql, data = (schedule_name))


    def update_schedules(self, param, data):
        sql = f"""UPDATE schedules SET {param} = ? WHERE schedule_name = ?""" 
        self.__executemany(sql, [data]) 


    def delete_schedule(self, schedule_id):
        sql = """DELETE FROM schedules WHERE schedule_id = ? """ 
        self.__executemany(sql, [(schedule_id)])
    
    def delete_group(self, schedule_id, group_id):
        sql = """DELETE FROM groups WHERE group_id = ? AND schedule_id = ? """ 
        self.__executemany(sql, [(group_id, schedule_id)])


if __name__ == '__main__':
    manager = DB_Manager(DATABASE)