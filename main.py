import sys
from datetime import datetime, timedelta
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from database import Database

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

class AccountingWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle('方海 - 记账系统')
        self.setGeometry(100, 100, 1400, 900)
        
        # 创建状态栏
        self.statusBar().showMessage('就绪')
        
        # 设置中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 创建标签页
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # 设置标签页样式
        self.tabs.setDocumentMode(False)
        self.tabs.setMovable(False)
        
        # 添加各个标签页
        self.setup_record_tab()
        self.setup_view_tab()
        self.setup_stats_tab()
        self.setup_category_tab()
        
    def setup_record_tab(self):
        self.record_tab = QWidget()
        self.tabs.addTab(self.record_tab, "记账录入")
        
        # 主布局 - 水平分割
        main_layout = QHBoxLayout(self.record_tab)
        main_layout.setSpacing(10)
        
        # 左侧：记账表单
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setSpacing(10)
        
        # 创建分组框
        group_box = QGroupBox("记账信息")
        group_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        form_layout = QGridLayout(group_box)
        form_layout.setSpacing(10)
        form_layout.setContentsMargins(20, 20, 20, 20)
        
        # 交易类型
        label_type = QLabel("交易类型：")
        label_type.setMinimumWidth(80)
        form_layout.addWidget(label_type, 0, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["支出", "收入"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        form_layout.addWidget(self.type_combo, 0, 1)
        
        # 分类
        label_category = QLabel("分类：")
        form_layout.addWidget(label_category, 1, 0)
        self.category_combo = QComboBox()
        form_layout.addWidget(self.category_combo, 1, 1)
        
        # 金额
        label_amount = QLabel("金额：")
        form_layout.addWidget(label_amount, 2, 0)
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("0.00")
        self.amount_edit.setValidator(QDoubleValidator(0, 9999999, 2))
        form_layout.addWidget(self.amount_edit, 2, 1)
        
        # 描述
        label_desc = QLabel("描述：")
        form_layout.addWidget(label_desc, 3, 0)
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("可选，请输入备注信息")
        form_layout.addWidget(self.desc_edit, 3, 1)
        
        # 日期
        label_date = QLabel("日期：")
        form_layout.addWidget(label_date, 4, 0)
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addWidget(self.date_edit, 4, 1)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.save_btn = QPushButton("保存记录")
        self.save_btn.setMinimumWidth(100)
        self.save_btn.clicked.connect(self.save_transaction)
        
        self.clear_btn = QPushButton("清空表单")
        self.clear_btn.setMinimumWidth(100)
        self.clear_btn.clicked.connect(self.clear_form)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.clear_btn)
        button_layout.addStretch()
        
        form_layout.addLayout(button_layout, 5, 0, 1, 2)
        
        left_layout.addWidget(group_box)
        left_layout.addStretch()
        
        # 右侧：本月记录列表
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(10)
        
        # 本月统计信息
        month_stats_group = QGroupBox("本月统计")
        month_stats_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        month_stats_layout = QHBoxLayout(month_stats_group)
        month_stats_layout.setSpacing(20)
        month_stats_layout.setContentsMargins(15, 10, 15, 10)
        
        self.month_income_label = QLabel("本月收入: ¥0.00")
        self.month_income_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 13px;")
        
        self.month_expense_label = QLabel("本月支出: ¥0.00")
        self.month_expense_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 13px;")
        
        self.month_balance_label = QLabel("本月结余: ¥0.00")
        self.month_balance_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        
        month_stats_layout.addWidget(self.month_income_label)
        month_stats_layout.addWidget(self.month_expense_label)
        month_stats_layout.addWidget(self.month_balance_label)
        month_stats_layout.addStretch()
        
        right_layout.addWidget(month_stats_group)
        
        # 本月记录列表
        month_list_group = QGroupBox("本月记录")
        month_list_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        month_list_layout = QVBoxLayout(month_list_group)
        
        self.month_table = QTableWidget()
        self.month_table.setAlternatingRowColors(True)
        self.month_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.month_table.setSelectionMode(QTableWidget.ExtendedSelection)  # 支持多选
        self.month_table.setColumnCount(5)
        self.month_table.setHorizontalHeaderLabels(["编号", "日期", "类型", "分类", "金额(¥)"])
        
        # 设置列宽
        self.month_table.setColumnWidth(0, 60)
        self.month_table.setColumnWidth(1, 100)
        self.month_table.setColumnWidth(2, 80)
        self.month_table.setColumnWidth(3, 100)
        self.month_table.horizontalHeader().setStretchLastSection(True)
        
        month_list_layout.addWidget(self.month_table)
        
        right_layout.addWidget(month_list_group)
        
        # 添加到主布局
        main_layout.addWidget(left_widget, 1)
        main_layout.addWidget(right_widget, 1)
        
        # 初始化分类和本月数据
        self.on_type_changed(self.type_combo.currentText())
        self.load_month_transactions()
        
    def setup_view_tab(self):
        self.view_tab = QWidget()
        self.tabs.addTab(self.view_tab, "记录查询")
        
        layout = QVBoxLayout(self.view_tab)
        layout.setSpacing(10)
        
        # 查询条件分组 - 所有条件放在同一行
        filter_group = QGroupBox("查询条件")
        filter_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        filter_layout = QHBoxLayout(filter_group)
        filter_layout.setSpacing(10)
        filter_layout.setContentsMargins(15, 10, 15, 10)
        
        # 日期范围
        filter_layout.addWidget(QLabel("开始日期："))
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setCalendarPopup(True)
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setFixedWidth(110)
        filter_layout.addWidget(self.start_date)
        
        filter_layout.addWidget(QLabel("至"))
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setFixedWidth(110)
        filter_layout.addWidget(self.end_date)
        
        # 分隔线
        filter_layout.addWidget(QLabel("|"))
        
        # 类型筛选
        filter_layout.addWidget(QLabel("交易类型："))
        self.filter_type = QComboBox()
        self.filter_type.addItems(["全部", "收入", "支出"])
        self.filter_type.setFixedWidth(100)
        filter_layout.addWidget(self.filter_type)
        
        filter_layout.addWidget(QLabel("分类："))
        self.filter_category = QComboBox()
        self.filter_category.addItem("全部", None)
        self.filter_category.setFixedWidth(120)
        filter_layout.addWidget(self.filter_category)
        
        filter_layout.addStretch()
        
        # 按钮
        self.query_btn = QPushButton("查询")
        self.query_btn.setFixedWidth(80)
        self.query_btn.clicked.connect(self.load_transactions)
        
        self.reset_btn = QPushButton("重置")
        self.reset_btn.setFixedWidth(80)
        self.reset_btn.clicked.connect(self.reset_query)
        
        self.print_btn = QPushButton("打印")
        self.print_btn.setFixedWidth(80)
        self.print_btn.clicked.connect(self.print_transactions)
        
        filter_layout.addWidget(self.query_btn)
        filter_layout.addWidget(self.reset_btn)
        filter_layout.addWidget(self.print_btn)
        
        layout.addWidget(filter_group)
        
        # 统计信息栏和批量删除按钮
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setSpacing(10)
        
        # 左侧统计信息
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        stats_layout.setSpacing(20)
        
        self.total_income_label = QLabel("总收入: ¥0.00")
        self.total_income_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 14px;")
        
        self.total_expense_label = QLabel("总支出: ¥0.00")
        self.total_expense_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 14px;")
        
        self.balance_label = QLabel("结余: ¥0.00")
        self.balance_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        
        self.record_count_label = QLabel("记录数: 0")
        self.record_count_label.setStyleSheet("color: #7f8c8d;")
        
        stats_layout.addWidget(self.total_income_label)
        stats_layout.addWidget(self.total_expense_label)
        stats_layout.addWidget(self.balance_label)
        stats_layout.addStretch()
        stats_layout.addWidget(self.record_count_label)
        
        # 右侧批量删除按钮
        self.batch_delete_btn = QPushButton("批量删除选中记录")
        self.batch_delete_btn.setFixedWidth(150)
        self.batch_delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.batch_delete_btn.clicked.connect(self.batch_delete_transactions)
        
        action_layout.addWidget(stats_widget)
        action_layout.addStretch()
        action_layout.addWidget(self.batch_delete_btn)
        
        layout.addWidget(action_widget)
        
        # 数据表格
        self.trans_table = QTableWidget()
        self.trans_table.setAlternatingRowColors(True)
        self.trans_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.trans_table.setSelectionMode(QTableWidget.ExtendedSelection)  # 支持多选
        self.trans_table.setColumnCount(6)
        self.trans_table.setHorizontalHeaderLabels(["编号", "日期", "类型", "分类", "金额(¥)", "备注"])
        
        # 设置列宽
        self.trans_table.setColumnWidth(0, 60)
        self.trans_table.setColumnWidth(1, 100)
        self.trans_table.setColumnWidth(2, 80)
        self.trans_table.setColumnWidth(3, 100)
        self.trans_table.setColumnWidth(4, 100)
        self.trans_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.trans_table)
        
        # 加载分类
        self.load_filter_categories()
        
    def setup_stats_tab(self):
        self.stats_tab = QWidget()
        self.tabs.addTab(self.stats_tab, "统计分析")
        
        layout = QVBoxLayout(self.stats_tab)
        layout.setSpacing(10)
        
        # 统计条件分组
        stats_group = QGroupBox("统计条件")
        stats_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        stats_layout = QHBoxLayout(stats_group)
        stats_layout.setSpacing(10)
        stats_layout.setContentsMargins(15, 10, 15, 10)
        
        # 时间区间选择
        stats_layout.addWidget(QLabel("统计区间："))
        
        self.stats_start_date = QDateEdit()
        self.stats_start_date.setDate(QDate.currentDate().addMonths(-1))
        self.stats_start_date.setCalendarPopup(True)
        self.stats_start_date.setDisplayFormat("yyyy-MM-dd")
        self.stats_start_date.setFixedWidth(110)
        stats_layout.addWidget(self.stats_start_date)
        
        stats_layout.addWidget(QLabel("至"))
        
        self.stats_end_date = QDateEdit()
        self.stats_end_date.setDate(QDate.currentDate())
        self.stats_end_date.setCalendarPopup(True)
        self.stats_end_date.setDisplayFormat("yyyy-MM-dd")
        self.stats_end_date.setFixedWidth(110)
        stats_layout.addWidget(self.stats_end_date)
        
        # 分隔线
        stats_layout.addWidget(QLabel("|"))
        
        # 快捷筛选按钮
        self.today_btn = QPushButton("今日")
        self.today_btn.setFixedWidth(50)
        self.today_btn.clicked.connect(self.set_today_range)
        
        self.week_btn = QPushButton("本周")
        self.week_btn.setFixedWidth(50)
        self.week_btn.clicked.connect(self.set_week_range)
        
        self.month_btn = QPushButton("本月")
        self.month_btn.setFixedWidth(50)
        self.month_btn.clicked.connect(self.set_month_range)
        
        self.year_btn = QPushButton("本年")
        self.year_btn.setFixedWidth(50)
        self.year_btn.clicked.connect(self.set_year_range)
        
        stats_layout.addWidget(self.today_btn)
        stats_layout.addWidget(self.week_btn)
        stats_layout.addWidget(self.month_btn)
        stats_layout.addWidget(self.year_btn)
        
        stats_layout.addStretch()
        
        # 生成统计按钮
        self.stats_btn = QPushButton("生成统计")
        self.stats_btn.setFixedWidth(100)
        self.stats_btn.clicked.connect(self.show_statistics)
        stats_layout.addWidget(self.stats_btn)
        
        layout.addWidget(stats_group)
        
        # 统计内容区域 - 水平分割（统计摘要和图表各占一半）
        content_widget = QWidget()
        content_layout = QHBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        # 左侧：统计摘要
        summary_group = QGroupBox("统计摘要")
        summary_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        summary_layout = QVBoxLayout(summary_group)
        summary_layout.setSpacing(10)
        summary_layout.setContentsMargins(10, 10, 10, 10)
        
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setMinimumHeight(500)
        self.summary_text.setStyleSheet("""
            QTextEdit {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 3px;
                font-size: 12px;
                font-family: "Microsoft YaHei";
                line-height: 1.5;
            }
        """)
        summary_layout.addWidget(self.summary_text)
        
        # 右侧：图表区域
        charts_group = QGroupBox("统计图表")
        charts_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        charts_layout = QVBoxLayout(charts_group)
        charts_layout.setSpacing(10)
        charts_layout.setContentsMargins(10, 10, 10, 10)
        
        # 柱状图
        bar_label = QLabel("支出分类统计图")
        bar_label.setAlignment(Qt.AlignCenter)
        bar_label.setStyleSheet("font-weight: bold; padding: 5px;")
        charts_layout.addWidget(bar_label)
        
        self.bar_canvas = FigureCanvas(Figure(figsize=(6, 3.5)))
        charts_layout.addWidget(self.bar_canvas)
        
        # 饼状图
        pie_label = QLabel("支出构成比例图")
        pie_label.setAlignment(Qt.AlignCenter)
        pie_label.setStyleSheet("font-weight: bold; padding: 5px; margin-top: 10px;")
        charts_layout.addWidget(pie_label)
        
        self.pie_canvas = FigureCanvas(Figure(figsize=(6, 3.5)))
        charts_layout.addWidget(self.pie_canvas)
        
        content_layout.addWidget(summary_group, 1)
        content_layout.addWidget(charts_group, 1)
        
        layout.addWidget(content_widget)
        
    def setup_category_tab(self):
        self.category_tab = QWidget()
        self.tabs.addTab(self.category_tab, "分类管理")
        
        layout = QVBoxLayout(self.category_tab)
        layout.setSpacing(10)
        
        # 添加分类分组
        add_group = QGroupBox("添加新分类")
        add_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        add_layout = QGridLayout(add_group)
        add_layout.setSpacing(8)
        add_layout.setContentsMargins(15, 15, 15, 15)
        
        add_layout.addWidget(QLabel("分类名称："), 0, 0)
        self.category_name = QLineEdit()
        self.category_name.setPlaceholderText("请输入分类名称")
        add_layout.addWidget(self.category_name, 0, 1)
        
        add_layout.addWidget(QLabel("分类类型："), 1, 0)
        self.category_type = QComboBox()
        self.category_type.addItems(["支出", "收入"])
        add_layout.addWidget(self.category_type, 1, 1)
        
        button_layout = QHBoxLayout()
        self.add_category_btn = QPushButton("添加分类")
        self.add_category_btn.setMinimumWidth(100)
        self.add_category_btn.clicked.connect(self.add_category)
        
        button_layout.addStretch()
        button_layout.addWidget(self.add_category_btn)
        button_layout.addStretch()
        
        add_layout.addLayout(button_layout, 2, 0, 1, 2)
        
        layout.addWidget(add_group)
        
        # 分类列表分组
        list_group = QGroupBox("现有分类")
        list_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
        """)
        
        list_layout = QVBoxLayout(list_group)
        
        # 分类表格和操作栏
        self.category_table = QTableWidget()
        self.category_table.setAlternatingRowColors(True)
        self.category_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.category_table.setSelectionMode(QTableWidget.ExtendedSelection)  # 支持多选
        self.category_table.setColumnCount(3)
        self.category_table.setHorizontalHeaderLabels(["编号", "分类名称", "类型"])
        self.category_table.setColumnWidth(0, 60)
        self.category_table.setColumnWidth(1, 200)
        self.category_table.horizontalHeader().setStretchLastSection(True)
        
        list_layout.addWidget(self.category_table)
        
        # 操作按钮栏
        action_layout = QHBoxLayout()
        
        self.delete_category_btn = QPushButton("删除选中分类")
        self.delete_category_btn.setMinimumWidth(120)
        self.delete_category_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.delete_category_btn.clicked.connect(self.delete_categories)
        
        action_layout.addStretch()
        action_layout.addWidget(self.delete_category_btn)
        action_layout.addStretch()
        
        list_layout.addLayout(action_layout)
        
        layout.addWidget(list_group)
        
        # 加载分类数据
        self.load_categories()
        
    def batch_delete_transactions(self):
        """批量删除选中的交易记录"""
        selected_rows = self.trans_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要删除的记录")
            return
        
        # 获取选中的记录ID
        selected_ids = []
        for row in selected_rows:
            id_item = self.trans_table.item(row.row(), 0)
            if id_item:
                selected_ids.append(int(id_item.text()))
        
        # 确认删除
        reply = QMessageBox.question(self, "确认删除", 
                                    f"确定要删除选中的 {len(selected_ids)} 条记录吗？\n此操作不可撤销！",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            success_count = 0
            fail_count = 0
            
            for record_id in selected_ids:
                try:
                    self.db.delete_transaction(record_id)
                    success_count += 1
                except Exception as e:
                    fail_count += 1
                    print(f"删除记录 {record_id} 失败: {str(e)}")
            
            # 刷新数据
            self.load_transactions()
            self.load_month_transactions()
            
            # 显示结果
            if fail_count == 0:
                QMessageBox.information(self, "成功", f"成功删除 {success_count} 条记录")
            else:
                QMessageBox.warning(self, "部分成功", f"成功删除 {success_count} 条记录\n失败 {fail_count} 条记录")
            
            self.statusBar().showMessage(f'已删除 {success_count} 条记录', 3000)
    
    def delete_categories(self):
        """批量删除选中的分类"""
        selected_rows = self.category_table.selectionModel().selectedRows()
        
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要删除的分类")
            return
        
        # 获取选中的分类ID和名称
        selected_categories = []
        for row in selected_rows:
            id_item = self.category_table.item(row.row(), 0)
            name_item = self.category_table.item(row.row(), 1)
            if id_item and name_item:
                selected_categories.append({
                    'id': int(id_item.text()),
                    'name': name_item.text()
                })
        
        # 确认删除
        category_names = "\n".join([f"• {cat['name']}" for cat in selected_categories])
        reply = QMessageBox.question(self, "确认删除", 
                                    f"确定要删除选中的 {len(selected_categories)} 个分类吗？\n\n{category_names}\n\n注意：有交易记录的分类无法删除！",
                                    QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            success_count = 0
            fail_count = 0
            failed_names = []
            
            for category in selected_categories:
                try:
                    self.db.delete_category(category['id'])
                    success_count += 1
                except ValueError as e:
                    fail_count += 1
                    failed_names.append(f"{category['name']} ({str(e)})")
                except Exception as e:
                    fail_count += 1
                    failed_names.append(f"{category['name']} (未知错误)")
            
            # 刷新数据
            self.load_categories()
            self.on_type_changed(self.type_combo.currentText())
            self.load_filter_categories()
            
            # 显示结果
            if fail_count == 0:
                QMessageBox.information(self, "成功", f"成功删除 {success_count} 个分类")
            else:
                error_msg = f"成功删除 {success_count} 个分类\n失败 {fail_count} 个分类：\n\n" + "\n".join(failed_names)
                QMessageBox.warning(self, "部分成功", error_msg)
            
            self.statusBar().showMessage(f'已删除 {success_count} 个分类', 3000)
        
    def load_month_transactions(self):
        """加载本月交易记录"""
        today = QDate.currentDate()
        start_date = QDate(today.year(), today.month(), 1).toString('yyyy-MM-dd')
        end_date = QDate(today.year(), today.month(), today.daysInMonth()).toString('yyyy-MM-dd')
        
        transactions = self.db.get_transactions(
            start_date=start_date,
            end_date=end_date
        )
        
        self.month_table.setRowCount(len(transactions))
        total_income = 0
        total_expense = 0
        
        for i, trans in enumerate(transactions):
            self.month_table.setItem(i, 0, QTableWidgetItem(str(trans['id'])))
            self.month_table.setItem(i, 1, QTableWidgetItem(trans['date']))
            self.month_table.setItem(i, 2, QTableWidgetItem('收入' if trans['type'] == 'income' else '支出'))
            self.month_table.setItem(i, 3, QTableWidgetItem(trans['category_name']))
            
            amount = trans['amount']
            amount_text = f"{amount:.2f}"
            self.month_table.setItem(i, 4, QTableWidgetItem(amount_text))
            
            if trans['type'] == 'income':
                total_income += amount
            else:
                total_expense += amount
        
        # 更新本月统计
        balance = total_income - total_expense
        self.month_income_label.setText(f"本月收入: ¥{total_income:.2f}")
        self.month_expense_label.setText(f"本月支出: ¥{total_expense:.2f}")
        
        if balance >= 0:
            self.month_balance_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 13px;")
        else:
            self.month_balance_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 13px;")
        self.month_balance_label.setText(f"本月结余: ¥{balance:.2f}")
        
    def set_today_range(self):
        """设置今日统计区间"""
        today = QDate.currentDate()
        self.stats_start_date.setDate(today)
        self.stats_end_date.setDate(today)
        self.show_statistics()
        
    def set_week_range(self):
        """设置本周统计区间"""
        today = QDate.currentDate()
        # 计算本周一
        weekday = today.dayOfWeek()
        monday = today.addDays(-(weekday - 1))
        sunday = monday.addDays(6)
        self.stats_start_date.setDate(monday)
        self.stats_end_date.setDate(sunday)
        self.show_statistics()
        
    def set_month_range(self):
        """设置本月统计区间"""
        today = QDate.currentDate()
        first_day = QDate(today.year(), today.month(), 1)
        last_day = QDate(today.year(), today.month(), today.daysInMonth())
        self.stats_start_date.setDate(first_day)
        self.stats_end_date.setDate(last_day)
        self.show_statistics()
        
    def set_year_range(self):
        """设置本年统计区间"""
        today = QDate.currentDate()
        first_day = QDate(today.year(), 1, 1)
        last_day = QDate(today.year(), 12, 31)
        self.stats_start_date.setDate(first_day)
        self.stats_end_date.setDate(last_day)
        self.show_statistics()
        
    def on_type_changed(self, type_text):
        self.category_combo.clear()
        db_type = 'expense' if type_text == '支出' else 'income'
        categories = self.db.get_categories(db_type)
        for cat in categories:
            self.category_combo.addItem(cat['name'], cat['id'])
            
    def save_transaction(self):
        try:
            amount_text = self.amount_edit.text().strip()
            if not amount_text:
                QMessageBox.warning(self, "提示", "请输入金额")
                return
                
            amount = float(amount_text)
            if amount <= 0:
                QMessageBox.warning(self, "提示", "金额必须大于0")
                return
                
            type_text = self.type_combo.currentText()
            db_type = 'expense' if type_text == '支出' else 'income'
            category_id = self.category_combo.currentData()
            description = self.desc_edit.text().strip()
            date = self.date_edit.date().toString('yyyy-MM-dd')
            
            self.db.add_transaction(category_id, amount, db_type, description, date)
            
            QMessageBox.information(self, "成功", "记账记录已保存")
            self.clear_form()
            
            # 刷新本月记录
            self.load_month_transactions()
            
            # 刷新当前显示的记录
            if self.tabs.currentIndex() == 1:  # 如果在查询标签页
                self.load_transactions()
                
            self.statusBar().showMessage('记录保存成功', 3000)
            
        except ValueError:
            QMessageBox.warning(self, "提示", "请输入有效的金额数字")
            
    def clear_form(self):
        self.amount_edit.clear()
        self.desc_edit.clear()
        self.date_edit.setDate(QDate.currentDate())
        
    def load_transactions(self):
        start_date = self.start_date.date().toString('yyyy-MM-dd')
        end_date = self.end_date.date().toString('yyyy-MM-dd')
        
        type_text = self.filter_type.currentText()
        db_type = None
        if type_text != "全部":
            db_type = 'expense' if type_text == '支出' else 'income'
            
        category_id = self.filter_category.currentData()
        if category_id is None:
            category_id = None
            
        transactions = self.db.get_transactions(
            category_id=category_id,
            type_=db_type,
            start_date=start_date,
            end_date=end_date
        )
        
        self.trans_table.setRowCount(len(transactions))
        total_income = 0
        total_expense = 0
        
        for i, trans in enumerate(transactions):
            self.trans_table.setItem(i, 0, QTableWidgetItem(str(trans['id'])))
            self.trans_table.setItem(i, 1, QTableWidgetItem(trans['date']))
            self.trans_table.setItem(i, 2, QTableWidgetItem('收入' if trans['type'] == 'income' else '支出'))
            self.trans_table.setItem(i, 3, QTableWidgetItem(trans['category_name']))
            
            amount = trans['amount']
            amount_text = f"{amount:.2f}"
            self.trans_table.setItem(i, 4, QTableWidgetItem(amount_text))
            self.trans_table.setItem(i, 5, QTableWidgetItem(trans['description'] or ''))
            
            # 统计
            if trans['type'] == 'income':
                total_income += amount
            else:
                total_expense += amount
        
        # 更新统计信息栏
        balance = total_income - total_expense
        self.total_income_label.setText(f"总收入: ¥{total_income:.2f}")
        self.total_expense_label.setText(f"总支出: ¥{total_expense:.2f}")
        self.balance_label.setText(f"结余: ¥{balance:.2f}")
        self.record_count_label.setText(f"记录数: {len(transactions)}")
        
        # 设置结余颜色
        if balance >= 0:
            self.balance_label.setStyleSheet("color: #27ae60; font-weight: bold; font-size: 14px;")
        else:
            self.balance_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 14px;")
        
        # 状态栏显示
        status_text = f"共 {len(transactions)} 条记录 | 总收入: ¥{total_income:.2f} | 总支出: ¥{total_expense:.2f} | 结余: ¥{balance:.2f}"
        self.statusBar().showMessage(status_text)
        
    def reset_query(self):
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.end_date.setDate(QDate.currentDate())
        self.filter_type.setCurrentIndex(0)
        self.filter_category.setCurrentIndex(0)
        self.load_transactions()
        
    def load_filter_categories(self):
        categories = self.db.get_categories()
        self.filter_category.clear()
        self.filter_category.addItem("全部", None)
        for cat in categories:
            type_text = '支出' if cat['type'] == 'expense' else '收入'
            self.filter_category.addItem(f"{cat['name']} ({type_text})", cat['id'])
            
    def print_transactions(self):
        printer = QPrinter(QPrinter.HighResolution)
        printer.setPageSize(QPrinter.A4)
        
        preview = QPrintPreviewDialog(printer, self)
        preview.paintRequested.connect(self.print_preview)
        preview.exec_()
        
    def print_preview(self, printer):
        # 计算统计信息
        total_income = 0
        total_expense = 0
        for row in range(self.trans_table.rowCount()):
            type_item = self.trans_table.item(row, 2)
            amount_item = self.trans_table.item(row, 4)
            if type_item and amount_item:
                amount = float(amount_item.text())
                if type_item.text() == '收入':
                    total_income += amount
                else:
                    total_expense += amount
        
        balance = total_income - total_expense
        
        # 生成打印内容
        doc = QTextDocument()
        
        html = """
        <html>
        <head>
        <style>
            body { font-family: SimHei, Microsoft YaHei; margin: 2cm; }
            h1 { color: #333; text-align: center; font-size: 18pt; }
            .info { background-color: #f5f5f5; padding: 10px; margin: 10px 0; border-radius: 5px; }
            .stats { margin: 20px 0; padding: 15px; background-color: #f9f9f9; border-left: 4px solid #3498db; }
            .stats p { margin: 5px 0; font-size: 12pt; }
            .income { color: #27ae60; font-weight: bold; }
            .expense { color: #e74c3c; font-weight: bold; }
            .balance { color: #2980b9; font-weight: bold; }
            table { border-collapse: collapse; width: 100%; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
            .footer { margin-top: 30px; text-align: center; color: #666; font-size: 10pt; }
        </style>
        </head>
        <body>
        """
        
        html += f"<h1>交易记录报表</h1>"
        html += f"<div class='info'>"
        html += f"<p><strong>查询期间：</strong> {self.start_date.date().toString('yyyy-MM-dd')} 至 {self.end_date.date().toString('yyyy-MM-dd')}</p>"
        html += f"<p><strong>生成时间：</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
        html += f"</div>"
        
        html += f"<div class='stats'>"
        html += f"<h3>📊 统计摘要</h3>"
        html += f"<p><span class='income'>💰 总收入：¥{total_income:,.2f}</span></p>"
        html += f"<p><span class='expense'>💸 总支出：¥{total_expense:,.2f}</span></p>"
        html += f"<p><span class='balance'>⚖️ 结余：¥{balance:,.2f}</span></p>"
        html += f"<p>📝 记录条数：{self.trans_table.rowCount()} 条</p>"
        if total_income > 0:
            expense_ratio = (total_expense / total_income * 100) if total_income > 0 else 0
            html += f"<p>📈 支出占收入比例：{expense_ratio:.1f}%</p>"
        html += f"</div>"
        
        html += "表格"
        html += "<tr><th>日期</th><th>类型</th><th>分类</th><th>金额(¥)</th><th>备注</th></tr>"
        
        for row in range(self.trans_table.rowCount()):
            html += "<tr>"
            for col in range(1, 6):  # 跳过ID列
                item = self.trans_table.item(row, col)
                cell_text = item.text() if item else ""
                # 为金额列添加样式
                if col == 4 and cell_text:
                    amount_value = float(cell_text)
                    if row < self.trans_table.rowCount():
                        type_item = self.trans_table.item(row, 2)
                        if type_item and type_item.text() == '收入':
                            html += f"<td class='income'>{cell_text}</td>"
                        else:
                            html += f"<td class='expense'>{cell_text}</td>"
                    else:
                        html += f"<td>{cell_text}</td>"
                else:
                    html += f"<td>{cell_text}</td>"
            html += "</tr>"
            
        html += "</table>"
        html += '<div class="footer">本报表由方海 - 记账系统生成</div>'
        html += "</body></html>"
        
        doc.setHtml(html)
        doc.print_(printer)
        
    def load_categories(self):
        categories = self.db.get_categories()
        self.category_table.setRowCount(len(categories))
        for i, cat in enumerate(categories):
            self.category_table.setItem(i, 0, QTableWidgetItem(str(cat['id'])))
            self.category_table.setItem(i, 1, QTableWidgetItem(cat['name']))
            self.category_table.setItem(i, 2, QTableWidgetItem('支出' if cat['type'] == 'expense' else '收入'))
            
    def add_category(self):
        name = self.category_name.text().strip()
        if not name:
            QMessageBox.warning(self, "提示", "请输入分类名称")
            return
            
        type_text = self.category_type.currentText()
        db_type = 'expense' if type_text == '支出' else 'income'
        
        try:
            self.db.add_category(name, db_type)
            QMessageBox.information(self, "成功", f"分类 '{name}' 添加成功")
            self.category_name.clear()
            self.load_categories()
            self.on_type_changed(self.type_combo.currentText())
            self.load_filter_categories()
            self.statusBar().showMessage('分类添加成功', 3000)
        except Exception as e:
            QMessageBox.warning(self, "错误", f"添加失败：{str(e)}")
            
    def delete_category(self):
        """保留单个删除功能（兼容旧代码）"""
        current_row = self.category_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "提示", "请先选择要删除的分类")
            return
            
        category_id = int(self.category_table.item(current_row, 0).text())
        category_name = self.category_table.item(current_row, 1).text()
        
        reply = QMessageBox.question(self, "确认删除", 
                                    f"确定要删除分类 '{category_name}' 吗？\n注意：有交易记录的分类无法删除。",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            try:
                self.db.delete_category(category_id)
                QMessageBox.information(self, "成功", f"分类 '{category_name}' 已删除")
                self.load_categories()
                self.on_type_changed(self.type_combo.currentText())
                self.load_filter_categories()
                self.statusBar().showMessage('分类删除成功', 3000)
            except ValueError as e:
                QMessageBox.warning(self, "提示", str(e))
                
    def show_statistics(self):
        start_date = self.stats_start_date.date().toString('yyyy-MM-dd')
        end_date = self.stats_end_date.date().toString('yyyy-MM-dd')
        stats = self.db.get_statistics(start_date, end_date)
        
        # 计算总收入、总支出、结余
        total_income = stats['total_income']
        total_expense = stats['total_expense']
        balance = total_income - total_expense
        
        # 计算各分类占比
        expense_items = []
        for item in stats['expense_by_category']:
            if item['total'] > 0:
                percentage = (item['total'] / total_expense * 100) if total_expense > 0 else 0
                expense_items.append({
                    'name': item['name'],
                    'amount': item['total'],
                    'percentage': percentage
                })
        
        income_items = []
        for item in stats['income_by_category']:
            if item['total'] > 0:
                percentage = (item['total'] / total_income * 100) if total_income > 0 else 0
                income_items.append({
                    'name': item['name'],
                    'amount': item['total'],
                    'percentage': percentage
                })
        
        # 生成完整的统计摘要
        summary = f"""
        <h3 style="color: #2c3e50; margin-top: 0; margin-bottom: 15px;">📊 财务统计报告</h3>
        
        <div style="background-color: #ecf0f1; padding: 12px; border-radius: 5px; margin: 10px 0;">
            <b>📅 统计区间：</b> {start_date} 至 {end_date}<br>
            <b>📈 统计天数：</b> {(datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days + 1} 天
        </div>
        
        <div style="margin: 20px 0;">
            <h4 style="color: #27ae60; margin: 5px 0;">💰 收入情况</h4>
            <div style="background-color: #e8f5e9; padding: 12px; border-radius: 5px;">
                <b>总收入：</b> <span style="font-size: 16px; color: #27ae60;">¥{total_income:,.2f}</span><br>
        """
        
        if income_items:
            summary += "<b style='margin-top: 8px; display: inline-block;'>收入明细：</b><br>"
            for item in income_items:
                summary += f"&nbsp;&nbsp;• {item['name']}: ¥{item['amount']:,.2f} ({item['percentage']:.1f}%)<br>"
        else:
            summary += "&nbsp;&nbsp;暂无收入记录<br>"
            
        summary += f"""
            </div>
        </div>
        
        <div style="margin: 20px 0;">
            <h4 style="color: #e74c3c; margin: 5px 0;">💸 支出情况</h4>
            <div style="background-color: #fee9e6; padding: 12px; border-radius: 5px;">
                <b>总支出：</b> <span style="font-size: 16px; color: #e74c3c;">¥{total_expense:,.2f}</span><br>
        """
        
        if expense_items:
            summary += "<b style='margin-top: 8px; display: inline-block;'>支出明细：</b><br>"
            for item in expense_items:
                summary += f"&nbsp;&nbsp;• {item['name']}: ¥{item['amount']:,.2f} ({item['percentage']:.1f}%)<br>"
        else:
            summary += "&nbsp;&nbsp;暂无支出记录<br>"
            
        summary += f"""
            </div>
        </div>
        
        <div style="margin: 20px 0;">
            <h4 style="color: #3498db; margin: 5px 0;">⚖️ 结余情况</h4>
            <div style="background-color: #e3f2fd; padding: 12px; border-radius: 5px;">
                <b>净结余：</b> <span style="font-size: 16px; color: {"#27ae60" if balance >= 0 else "#e74c3c"};">¥{balance:,.2f}</span><br>
        """
        
        if total_income > 0:
            expense_ratio = (total_expense / total_income * 100)
            status = "✅ 健康" if total_expense <= total_income else "⚠️ 超支"
            summary += f"<b>支出占收入比例：</b> {expense_ratio:.1f}% {status}<br>"
        else:
            summary += "<b>支出占收入比例：</b> 无收入数据<br>"
            
        summary += f"""
            </div>
        </div>
        
        <div style="margin-top: 20px; padding-top: 10px; border-top: 1px solid #ddd; color: #7f8c8d; font-size: 11px;">
            <i>注：以上统计基于所选时间区间内的所有交易记录</i>
        </div>
        """
        
        self.summary_text.setHtml(summary)
        
        # 绘制图表
        self.draw_bar_chart(stats)
        self.draw_pie_chart(stats)
        
        self.statusBar().showMessage(f'统计完成：{start_date} 至 {end_date}', 3000)
        
    def draw_bar_chart(self, stats):
        self.bar_canvas.figure.clear()
        ax = self.bar_canvas.figure.add_subplot(111)
        
        # 准备数据
        expense_data = [(item['name'], item['total']) for item in stats['expense_by_category'] if item['total'] > 0]
        
        if expense_data:
            categories = [item[0] for item in expense_data]
            values = [item[1] for item in expense_data]
            
            # 绘制柱状图
            colors = plt.cm.RdYlGn_r([i/len(values) for i in range(len(values))])
            bars = ax.bar(range(len(categories)), values, color=colors, alpha=0.8)
            
            # 设置标签
            ax.set_xlabel('支出分类', fontsize=10)
            ax.set_ylabel('金额 (元)', fontsize=10)
            ax.set_title('各分类支出金额对比', fontsize=12, fontweight='bold')
            ax.set_xticks(range(len(categories)))
            ax.set_xticklabels(categories, rotation=45, ha='right')
            
            # 添加网格
            ax.grid(axis='y', alpha=0.3, linestyle='--')
            
            # 添加数值标签
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{value:,.0f}', ha='center', va='bottom', fontsize=9)
        else:
            ax.text(0.5, 0.5, '暂无支出数据', ha='center', va='center', transform=ax.transAxes,
                   fontsize=12, color='gray')
            ax.set_title('支出分类统计', fontsize=12, fontweight='bold')
            
        self.bar_canvas.figure.tight_layout()
        self.bar_canvas.draw()
        
    def draw_pie_chart(self, stats):
        self.pie_canvas.figure.clear()
        ax = self.pie_canvas.figure.add_subplot(111)
        
        # 准备数据
        expense_data = [(item['name'], item['total']) for item in stats['expense_by_category'] if item['total'] > 0]
        
        if expense_data:
            categories = [item[0] for item in expense_data]
            values = [item[1] for item in expense_data]
            
            # 绘制饼图
            colors = plt.cm.Set3(range(len(categories)))
            wedges, texts, autotexts = ax.pie(values, labels=categories, autopct='%1.1f%%',
                                                startangle=90, colors=colors)
            
            ax.set_title('支出构成比例', fontsize=12, fontweight='bold')
            
            # 美化文本
            for text in texts:
                text.set_fontsize(9)
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(10)
                autotext.set_weight('bold')
        else:
            ax.text(0.5, 0.5, '暂无支出数据', ha='center', va='center', transform=ax.transAxes,
                   fontsize=12, color='gray')
            ax.set_title('支出构成比例', fontsize=12, fontweight='bold')
            
        self.pie_canvas.figure.tight_layout()
        self.pie_canvas.draw()

def main():
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 9)
    app.setFont(font)
    
    window = AccountingWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()