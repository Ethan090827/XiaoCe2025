# app.py
from flask import Flask, render_template, request, jsonify, session, redirect
import json
import random
from datetime import datetime
from collections import deque, defaultdict
import heapq
from typing import List, Dict, Tuple, Set
import csv
import os

app = Flask(__name__)
app.secret_key = 'shanghai-metro-guess-secret-key-2024'
current_path = os.getcwd()
print(current_path)

class ShanghaiMetroGraph:
    """上海地铁网络图"""
    
    def __init__(self):
        # 初始化数据结构
        self.stations = {}  # 站点信息
        self.lines = {}     # 线路信息
        self.graph = defaultdict(list)  # 邻接表表示的地铁网络
        self.station_lines = defaultdict(set)  # 站点对应的线路
        self.station_nodes = {}  # 站点节点映射（支持同站不同线）
        
        # 用于存储预计算的最短距离和换乘次数
        self.shortest_routes = {}
        self.minimum_changes = {}
        
        # 初始化数据
        self.load_stations()
        self.load_distances_and_changes()

    def load_distances_and_changes(self):
        """加载预计算的最短距离和最少换乘次数"""
        # 加载最短站数
        try:
            with open(current_path+'/data/ShortestRoute.csv', 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)  # 第一行是站名
                stations = [row[0] for row in reader] # 获取所有站名
                f.seek(0) # 重置文件指针
                next(reader) # 跳过标题行
                for i, row in enumerate(reader):
                    from_station = header[i + 1] # 第一列是站名，所以取 i+1
                    for j, value in enumerate(row[1:]): # 跳过第一列
                        to_station = stations[j]
                        if from_station not in self.shortest_routes:
                            self.shortest_routes[from_station] = {}
                        self.shortest_routes[from_station][to_station] = int(value)
        except FileNotFoundError:
            print("Warning: ShortestRoute.csv not found. Calculating distances will fail.")
        except Exception as e:
            print(f"Error loading shortest routes: {e}")

        # 加载最少换乘次数
        try:
            with open(current_path+'/data/MinimumChange.csv', 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)  # 第一行是站名
                stations = [row[0] for row in reader] # 获取所有站名
                f.seek(0) # 重置文件指针
                next(reader) # 跳过标题行
                for i, row in enumerate(reader):
                    from_station = header[i + 1] # 第一列是站名，所以取 i+1
                    for j, value in enumerate(row[1:]): # 跳过第一列
                        to_station = stations[j]
                        if from_station not in self.minimum_changes:
                            self.minimum_changes[from_station] = {}
                        self.minimum_changes[from_station][to_station] = int(value)
        except FileNotFoundError:
            print("Warning: MinimumChange.csv not found. Calculating transfers will fail.")
        except Exception as e:
            print(f"Error loading minimum changes: {e}")

    def load_stations(self):
        """加载上海地铁站点数据"""
        try:
            with open(current_path+'/data/StationInfo.csv', 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row['站名']
                    district = row['区县']
                    # 解析线路，非空值才加入列表
                    lines = [row[f'线路{i}'] for i in range(1, 6) if row[f'线路{i}']]
                    try:
                        opening_year = int(row['开通年份']) if row['开通年份'] else 0
                    except ValueError:
                        opening_year = 0 # 如果年份不是数字，则设为0

                    # 存储站点信息
                    self.stations[name] = {
                        "district": district,
                        "lines": lines,
                        "opening_year": opening_year,
                    }
                    
                    # 存储站点线路关系
                    for line in lines:
                        if line not in self.lines:
                            self.lines[line] = []
                        if name not in self.lines[line]:
                            self.lines[line].append(name)
                        
                    # 创建站点节点（考虑同站不同线的情况）
                    for line in lines:
                        node_id = f"{name}_{line}"
                        self.station_nodes[node_id] = {
                            "station_name": name,
                            "line": line,
                        }
        except FileNotFoundError:
            print("Error: StationInfo.csv not found.")
        except Exception as e:
            print(f"Error loading station info: {e}")
    
    def calculate_min_stations(self, start_station: str, end_station: str) -> int:
        """计算最小站数 - 从预加载的CSV数据中获取"""
        if start_station in self.shortest_routes and end_station in self.shortest_routes[start_station]:
            return self.shortest_routes[start_station][end_station]
        else:
            # 如果站点不存在于预计算数据中，返回一个大值或默认值
            # 例如，如果CSV数据是完整的，理论上不会走到这里
            # 但为了健壮性，可以返回一个表示“无穷”的值
            return 100

    def calculate_min_transfers(self, start_station: str, end_station: str) -> int:
        """计算最小换乘次数 - 从预加载的CSV数据中获取"""
        if start_station in self.minimum_changes and end_station in self.minimum_changes[start_station]:
            return self.minimum_changes[start_station][end_station]
        else:
            # 如果站点不存在于预计算数据中，返回一个大值或默认值
            return 10


    def get_all_stations(self) -> List[str]:
        """获取所有站点列表"""
        return sorted(list(self.stations.keys()))
    
    def get_station_info(self, station_name: str) -> Dict:
        """获取站点信息"""
        return self.stations.get(station_name, {})

# 初始化地铁图
metro_graph = ShanghaiMetroGraph()

@app.route('/')
def index():
    """首页 - 输入班级姓名"""
    session.clear()
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    """处理登录信息"""
    class_name = request.form.get('class_name')
    student_name = request.form.get('student_name')
    
    if class_name and student_name:
        session['class'] = class_name
        session['name'] = student_name
        session['game_state'] = 'menu'
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/menu')
def menu():
    """选择界面"""
    if 'class' not in session:
        return redirect('/')
    return render_template('menu.html')

@app.route('/start_game/<game_type>')
def start_game(game_type):
    """开始游戏"""
    if game_type == 'metro_guess':
        # 随机选择答案
        all_stations = metro_graph.get_all_stations()
        ans = "none"
        # ans = input("请指定答案，输入“none”随机生成")
        if ans == "none":
            answer = random.choice(all_stations)
        else:
            answer = ans
        session['game_type'] = 'metro_guess'
        session['answer'] = answer
        session['guesses'] = []
        session['attempts'] = 0
        session['max_attempts'] = 6
        session['game_over'] = False
        
        # 测试输出
        print(f"游戏开始 - 答案: {answer}")
        
        return render_template('metro_game.html',
                               stations=all_stations)
    
    return redirect('/menu')

@app.route('/submit_guess', methods=['POST'])
def submit_guess():
    """处理猜测"""
    if session.get('game_over'):
        return jsonify({'game_over': True})
    
    guess = request.json.get('guess')
    answer = session.get('answer')
    
    if not guess or not answer:
        return jsonify({'error': '数据错误'})
    
    # 获取站点信息
    guess_info = metro_graph.get_station_info(guess)
    answer_info = metro_graph.get_station_info(answer)
    
    if not guess_info or not answer_info:
        return jsonify({'error': '站点信息不存在'})
    
    # 计算最小站数和换乘次数 (现在从CSV数据获取)
    min_stations = metro_graph.calculate_min_stations(guess, answer)
    min_transfers = metro_graph.calculate_min_transfers(guess, answer)
    
    # 线路比较
    guess_lines = set(guess_info.get('lines', []))
    answer_lines = set(answer_info.get('lines', []))
    intersection = guess_lines & answer_lines
    
    if guess_lines == answer_lines:
        lines_match = 'perfect'  # 完全正确
    elif intersection:
        lines_match = 'partial'  # 部分正确
    else:
        lines_match = 'none'     # 完全不匹配
    
    # 年份比较
    opening_year_guess = guess_info.get('opening_year', 0)
    opening_year_answer = answer_info.get('opening_year', 0)
    
    year_relation = 'same'
    if opening_year_guess > opening_year_answer:
        year_relation = 'later'
    elif opening_year_guess < opening_year_answer:
        year_relation = 'earlier'
    
    # 创建结果
    result = {
        'guess': guess,
        'district_match': guess_info.get('district') == answer_info.get('district'),
        'district_guess': guess_info.get('district', ''),
        'district_answer': answer_info.get('district', ''),
        'lines_guess': list(guess_lines),
        'lines_answer': list(answer_lines),
        'lines_match': lines_match,
        'opening_year_guess': opening_year_guess,
        'opening_year_answer': opening_year_answer,
        'year_relation': year_relation,
        'min_stations': min_stations,
        'min_transfers': min_transfers,
        'is_correct': guess == answer
    }
    
    # 添加到猜测记录
    guesses = session.get('guesses', [])
    guesses.append(result)
    session['guesses'] = guesses
    
    # 更新尝试次数
    attempts = session.get('attempts', 0) + 1
    session['attempts'] = attempts
    
    # 检查游戏是否结束
    game_over = False
    if guess == answer:
        game_over = True
        session['game_over'] = True
    elif attempts >= session.get('max_attempts', 6):
        game_over = True
        session['game_over'] = True
    
    session.modified = True
    
    response_data = {
        'result': result,
        'attempts_left': session.get('max_attempts', 6) - attempts,
        'game_over': game_over
    }
    
    # 只有在游戏结束且没有猜对的情况下才返回答案
    if game_over and guess != answer:
        response_data['answer'] = answer
    
    return jsonify(response_data)

@app.route('/end_game')
def end_game():
    """结束游戏返回菜单"""
    session['game_state'] = 'menu'
    return redirect('/menu')

@app.route('/get_station_info/<station_name>')
def get_station_info(station_name):
    """获取站点信息API"""
    info = metro_graph.get_station_info(station_name)
    if info:
        return jsonify({'success': True, 'info': info})
    return jsonify({'success': False, 'error': '站点不存在'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)