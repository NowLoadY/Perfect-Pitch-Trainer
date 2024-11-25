import random
import pygame
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QLineEdit, QVBoxLayout, QWidget, QMessageBox, QComboBox, QHBoxLayout, QProgressBar
import pygame.midi
from PyQt5.QtCore import QTimer, QEasingCurve, QPropertyAnimation, QRect


class PerfectPitchTrainer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.difficulty_levels = {
            'Simple': ['C', 'D', 'E'],
            'Advanced': ['C', 'D', 'E', 'F', 'G'],
            'C Scale': ['C', 'D', 'E', 'F', 'G', 'A', 'B'],
            'Chromatic': ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        }
        self.current_level = 'Simple'
        self.note_to_midi = {
            'C': 60, 'C#': 61, 'D': 62, 'D#': 63, 'E': 64, 'F': 65, 'F#': 66,
            'G': 67, 'G#': 68, 'A': 69, 'A#': 70, 'B': 71
        }
        self.midi_to_note = {v: k for k, v in self.note_to_midi.items()}
        self.total_questions = 0
        pygame.midi.init()
        self.midi_output = pygame.midi.Output(pygame.midi.get_default_output_id())
        pygame.mixer.init()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Perfect Pitch Trainer')
        self.setGeometry(300, 100, 800, 500)

        self.layout = QVBoxLayout()

        self.label = QLabel('Set Number of Questions:')
        self.label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.layout.addWidget(self.label)

        self.input_field = QLineEdit(self)
        self.input_field.setPlaceholderText("Enter a number")
        self.input_field.setStyleSheet("font-size: 20px;")
        self.layout.addWidget(self.input_field)

        self.difficulty_label = QLabel('Select Difficulty:')
        self.difficulty_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.layout.addWidget(self.difficulty_label)

        self.difficulty_combo = QComboBox(self)
        self.difficulty_combo.addItems(self.difficulty_levels.keys())
        self.difficulty_combo.currentTextChanged.connect(self.set_difficulty)
        self.difficulty_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #333333;
                border-radius: 5px;
                padding: 10px;
                font-size: 24px;
                height: 40px;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 30px; /* 下拉箭头宽度 */
                border-left: 1px solid #333333;
            }
            """)
        self.layout.addWidget(self.difficulty_combo)

        self.start_button = QPushButton('Start', self)
        QPB_StyleSheet_0 = generate_QPB_style(background_color="#333333", text_color="white", border_color="#333333",
                           border_radius=8, padding=15, font_size=24, font_weight="bold")
        self.start_button.setStyleSheet(QPB_StyleSheet_0+"""
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #666666, stop: 1 #333333
                );
            }
            QPushButton:pressed {
                background-color: #000000;
            }
        """)
        self.start_button.clicked.connect(self.start_test)
        self.layout.addWidget(self.start_button)

        self.main_widget = QWidget(self)
        self.main_widget.setLayout(self.layout)
        self.main_widget.setStyleSheet("""
            background-color: #ffffff;
            color: #333333;
            font-family: Arial, sans-serif;
            font-size: 16px;
            border-radius: 8px;
            padding: 20px;
            """)
        self.setCentralWidget(self.main_widget)

        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(500)
        self.animation.setStartValue(0)
        self.animation.setEndValue(1)
        self.animation.start()


    def set_difficulty(self, level):
        self.current_level = level

    def start_test(self):
        try:
            self.total_questions = int(self.input_field.text())
            self.show_answer_page()
        except ValueError:
            QMessageBox.warning(self, "Input Error", "Please enter a valid number")

    def show_answer_page(self):
        self.answer_page = AnswerPage(self.total_questions, self.current_level, self.note_to_midi, self.midi_to_note, self.difficulty_levels, self.midi_output)
        self.answer_page.show()


class AnswerPage(QMainWindow):
    def __init__(self, total_questions, current_level, note_to_midi, midi_to_note, difficulty_levels, midi_output):
        super().__init__()
        self.total_questions = total_questions
        self.current_level = current_level
        self.note_to_midi = note_to_midi
        self.midi_to_note = midi_to_note
        self.difficulty_levels = difficulty_levels
        self.correct_count = 0
        self.current_question = 0
        self.results = []
        self.correct_note = ''
        self.answer_selected_flag = False
        self.is_correct = False  # Initialize correct answer flag
        self.midi_out = midi_output
        self.initUI()
        self.start_test()

    def initUI(self):
        self.setWindowTitle('Answer Page')
        self.setGeometry(600, 100, 500, 350)
        self.layout = QVBoxLayout()
        self.layout.setSpacing(15)

        # 显示结果标签
        self.result_label = QLabel('', self)
        self.result_label.setStyleSheet("""
            QLabel {
                color: #000000;
                font-family: Arial;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        self.layout.addWidget(self.result_label)

        # 答案按钮布局
        self.answer_buttons_layout = QHBoxLayout()
        self.answer_buttons = []
        QPB_StyleSheet_1 = generate_QPB_style()
        QPB_StyleSheet_2 = generate_QPB_style(background_color="#FFFFFF", text_color="#000000", border_color="#000000",
                                              border_radius=16, padding=10, font_family="Arial", font_size=24, font_weight="bold")
        for note in self.difficulty_levels[self.current_level]:
            button = QPushButton(note, self)
            button.setStyleSheet(QPB_StyleSheet_2+"""
                QPushButton:hover {
                    background-color: #F0F0F0;  /* 浅灰色 */
                }
                QPushButton:pressed {
                    background-color: #E0E0E0;  /* 更深的灰色 */
                }
            """)
            button.clicked.connect(lambda checked, n=note: self.answer_selected(n))
            self.answer_buttons.append(button)
            self.answer_buttons_layout.addWidget(button)
        self.layout.addLayout(self.answer_buttons_layout)

        # 重复音符按钮
        self.repeat_button = QPushButton('Replay Note', self)
        self.repeat_button.setStyleSheet(QPB_StyleSheet_1+"""
            QPushButton:hover {
                background-color: #F0F0F0;
            }
            QPushButton:pressed {
                background-color: #E0E0E0;
            }
        """)
        self.repeat_button.clicked.connect(self.repeat_note)
        self.layout.addWidget(self.repeat_button)

        # 下一题按钮
        self.next_button = QPushButton('Next', self)
        self.next_button.setStyleSheet(QPB_StyleSheet_1+"""

            QPushButton:hover {
                background-color: #F0F0F0;
            }
            QPushButton:pressed {
                background-color: #E0E0E0;
            }
        """)
        self.next_button.clicked.connect(self.next_question)
        self.layout.addWidget(self.next_button)

        # 设置主窗口小部件
        self.main_widget = QWidget(self)
        self.main_widget.setLayout(self.layout)
        self.main_widget.setStyleSheet("background-color: #FFFFFF; padding: 20px;")  # 白色背景
        self.setCentralWidget(self.main_widget)

        # 定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer_timeout)

        # 添加进度条
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMaximum(self.total_questions)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #FFFFFF; 
                border: 1px solid #000000;
                border-radius: 5px;
                text-align: center;
                color: #000000;
            }
            QProgressBar::chunk {
                background-color: #000000; 
                border-radius: 5px;
            }
        """)
        self.layout.addWidget(self.progress_bar)

        # 添加窗口淡入动画
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(500)  # 动画持续时间
        self.animation.setStartValue(0)   # 从透明开始
        self.animation.setEndValue(1)     # 到完全显示
        self.animation.start()

    def start_test(self):
        self.next_question(init=True)

    def play_note_midi(self, midi_note):
        self.midi_out.note_on(midi_note, 64)
        self.timer.start(1500)

    def on_timer_timeout(self):
        self.midi_out.note_off(self.current_midi_note, 64)
        self.timer.stop()

    def repeat_note(self):
        if hasattr(self, 'current_midi_note'):  # 检查当前音符是否存在
            self.play_note_midi(self.current_midi_note)  # 重新播放当前音符

    def next_question(self, init=False):
        if not init:
            if not self.answer_selected_flag:
                self.next_button.setText("Please complete the current question first")
                QTimer.singleShot(2000, lambda: self.next_button.setText("Next Question"))
                return

        self.answer_selected_flag = False
        self.is_correct = False

        if self.current_question < self.total_questions:
            self.current_question += 1
            self.current_midi_note = self.generate_random_note_midi()
            self.play_note_midi(self.current_midi_note)
            self.correct_note = self.midi_to_note[self.current_midi_note]
            
            self.progress_bar.setValue(self.current_question)

            self.update_result_label(f"Current Question: {self.current_question}/{self.total_questions}")
        else:
            self.show_results()

    def generate_random_note_midi(self):
        while True:
            note_name = random.choice(self.difficulty_levels[self.current_level])
            new_midi_note = self.note_to_midi[note_name]
            # 确保新生成的音符与当前音符不同
            if not hasattr(self, 'current_midi_note') or new_midi_note != self.current_midi_note:
                return new_midi_note
    
    def play_note_midi(self, midi_note):
        # 发送note_on消息
        self.midi_out.note_on(midi_note, 64)
        self.timer.start(1500)  # 设置定时器为1500毫秒后触发

    def on_timer_timeout(self):
        # 发送note_off消息
        self.midi_out.note_off(self.current_midi_note, 64)
        self.timer.stop()  # 停止定时器

    def answer_selected(self, user_input):
        if not self.answer_selected_flag:
            self.answer_selected_flag = True
            selected_button = [button for button in self.answer_buttons if button.text() == user_input][0]
            
            # 设置放大动画
            self.scale_animation = QPropertyAnimation(selected_button, b"geometry")
            self.scale_animation.setDuration(150)
            self.scale_animation.setStartValue(selected_button.geometry())
            
            # 放大按钮尺寸
            start_rect = selected_button.geometry()
            scale_rect = QRect(start_rect.x() - 5, start_rect.y() - 5, start_rect.width() + 10, start_rect.height() + 10)
            self.scale_animation.setEndValue(scale_rect)
            
            # 添加平滑的缓入缓出效果
            self.scale_animation.setEasingCurve(QEasingCurve.InOutQuad)
            self.scale_animation.start()
            
            # 继续原有逻辑
            self.results.append((self.correct_note, user_input))
            if self.check_answer(user_input, self.correct_note):
                self.correct_count += 1
                self.is_correct = True
                self.update_result_label("Correct")
            else:
                self.is_correct = False
                self.update_result_label("Incorrect Answer")
        else:
            # 如果已答对当前题目，点击任意选项都会播放对应音符的音频
            if self.is_correct:
                self.play_note_midi(self.note_to_midi[user_input])  # 播放所选音符的音频
            else:
                self.update_result_label("Correct, but no points awarded")
                self.play_note_midi(self.note_to_midi[user_input])  # 播放所选音符的音频

    def check_answer(self, user_input, correct_note):
        return user_input.strip().upper() == correct_note

    def update_result_label(self, text):
        self.result_label.setText(text)

    def show_results(self):
        result_text = "Results:\n"
        for correct, user in self.results:
            result_text += f"Correct Note: {correct}, Your Answer: {user}\n"
        result_text += f"Accuracy: {int(self.correct_count/self.total_questions*100)}%"

        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.NoIcon)  # 去掉默认图标
        msg.setWindowTitle("Test Finished")
        msg.setText(result_text)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #FFFFFF;  /* 背景使用白色 */
                border: 2px solid #333333;  /* 黑色边框 */
                border-radius: 10px;
                padding: 15px;
            }
            QMessageBox QLabel {
                font-size: 16px;
                color: #333333;  /* 黑色字体 */
                font-family: 'Arial', sans-serif;
                margin-bottom: 10px;
            }
            QMessageBox QPushButton {
                background-color: #FFFFFF;  /* 白色背景 */
                color: #333333;  /* 黑色文字 */
                border: 2px solid #333333;  /* 黑色边框 */
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                padding: 10px 15px;
                margin-top: 10px;
            }
            QMessageBox QPushButton:hover {
                background-color: #F0F0F0;  /* 按钮悬停效果：浅灰色 */
            }
            QMessageBox QPushButton:pressed {
                background-color: #DDDDDD;  /* 按钮按下效果：更深的灰色 */
            }
        """)
        # 显示消息框
        msg.exec_()
        self.close()


def generate_QPB_style(background_color="#FFFFFF", text_color="#000000", border_color="#000000", 
                   border_radius=8, padding=8, font_family="Arial", font_size=24, font_weight="normal"):
    return f"""
        QPushButton {{
            background-color: {background_color};
            color: {text_color};
            border: 2px solid {border_color};
            border-radius: {border_radius}px;
            padding: {padding}px;
            font-family: {font_family};
            font-size: {font_size}px;
            font-weight: {font_weight};
        }}
    """


if __name__ == '__main__':
    app = QApplication(sys.argv)
    trainer = PerfectPitchTrainer()
    trainer.show()
    sys.exit(app.exec_())
