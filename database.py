import sqlite3
from datetime import datetime, timedelta
from contextlib import contextmanager

class Database:
    def __init__(self, db_path='accounting.db'):
        self.db_path = db_path
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建分类表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建交易记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                    description TEXT,
                    date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories(id)
                )
            ''')
            
            # 插入默认分类
            default_categories = [
                ('工资', 'income'), ('奖金', 'income'), ('投资', 'income'),
                ('餐饮', 'expense'), ('交通', 'expense'), ('购物', 'expense'),
                ('娱乐', 'expense'), ('医疗', 'expense'), ('教育', 'expense')
            ]
            
            for name, type_ in default_categories:
                cursor.execute('''
                    INSERT OR IGNORE INTO categories (name, type) VALUES (?, ?)
                ''', (name, type_))
    
    # 分类操作
    def add_category(self, name, type_):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO categories (name, type) VALUES (?, ?)
            ''', (name, type_))
            return cursor.lastrowid
    
    def get_categories(self, type_=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if type_:
                cursor.execute('''
                    SELECT * FROM categories WHERE type = ? ORDER BY name
                ''', (type_,))
            else:
                cursor.execute('SELECT * FROM categories ORDER BY type, name')
            return cursor.fetchall()
    
    def delete_category(self, category_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 检查是否有交易记录使用此分类
            cursor.execute('SELECT COUNT(*) FROM transactions WHERE category_id = ?', (category_id,))
            count = cursor.fetchone()[0]
            if count > 0:
                raise ValueError('该分类下存在交易记录，无法删除')
            cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
    
    # 交易记录操作
    def add_transaction(self, category_id, amount, type_, description, date):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions (category_id, amount, type, description, date)
                VALUES (?, ?, ?, ?, ?)
            ''', (category_id, amount, type_, description, date))
            return cursor.lastrowid
    
    def get_transactions(self, category_id=None, type_=None, start_date=None, end_date=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = '''
                SELECT t.*, c.name as category_name 
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE 1=1
            '''
            params = []
            
            if category_id:
                query += ' AND t.category_id = ?'
                params.append(category_id)
            if type_:
                query += ' AND t.type = ?'
                params.append(type_)
            if start_date:
                query += ' AND t.date >= ?'
                params.append(start_date)
            if end_date:
                query += ' AND t.date <= ?'
                params.append(end_date)
            
            query += ' ORDER BY t.date DESC, t.created_at DESC'
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def delete_transaction(self, transaction_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
    
    def update_transaction(self, transaction_id, category_id, amount, type_, description, date):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE transactions 
                SET category_id = ?, amount = ?, type = ?, description = ?, date = ?
                WHERE id = ?
            ''', (category_id, amount, type_, description, date, transaction_id))
    
    # 统计功能
    def get_statistics(self, start_date, end_date):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 总收入
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM transactions 
                WHERE type = 'income' AND date BETWEEN ? AND ?
            ''', (start_date, end_date))
            total_income = cursor.fetchone()[0]
            
            # 总支出
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM transactions 
                WHERE type = 'expense' AND date BETWEEN ? AND ?
            ''', (start_date, end_date))
            total_expense = cursor.fetchone()[0]
            
            # 按分类统计支出
            cursor.execute('''
                SELECT c.name, COALESCE(SUM(t.amount), 0) as total
                FROM categories c
                LEFT JOIN transactions t ON c.id = t.category_id 
                    AND t.type = 'expense' AND t.date BETWEEN ? AND ?
                WHERE c.type = 'expense'
                GROUP BY c.id, c.name
                ORDER BY total DESC
            ''', (start_date, end_date))
            expense_by_category = cursor.fetchall()
            
            # 按分类统计收入
            cursor.execute('''
                SELECT c.name, COALESCE(SUM(t.amount), 0) as total
                FROM categories c
                LEFT JOIN transactions t ON c.id = t.category_id 
                    AND t.type = 'income' AND t.date BETWEEN ? AND ?
                WHERE c.type = 'income'
                GROUP BY c.id, c.name
                ORDER BY total DESC
            ''', (start_date, end_date))
            income_by_category = cursor.fetchall()
            
            return {
                'total_income': total_income,
                'total_expense': total_expense,
                'expense_by_category': expense_by_category,
                'income_by_category': income_by_category
            }