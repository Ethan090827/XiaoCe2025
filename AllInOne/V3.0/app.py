# app.py
from flask import Flask, render_template, request, jsonify, session, redirect
import json
import random
from datetime import datetime
from collections import deque, defaultdict
from typing import List, Dict
import csv
import os

app = Flask(__name__)
app.secret_key = 'shanghai-metro-guess-secret-key-2024'

class Leaderboard:
    def __init__(self, filename='Leaderboard.csv'):
        self.filename = filename
        self.data = []
        self.load()

    def load(self):
        """从CSV文件加载排行榜数据"""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r', newline='', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    self.data = [row for row in reader]
            except Exception as e:
                print(f"Error loading leaderboard: {e}")
                self.data = []
        else:
            # 如果文件不存在，创建一个带表头的空文件
            # 表头包括通用字段和三个模块的字段
            with open(self.filename, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['timestamp', 'class', 'name', '猜铁_success', '猜铁_attempts', '国景_success', '国景_attempts', '填国_success', '填国_attempts']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
            self.data = []

    def save(self):
        """将排行榜数据保存到CSV文件"""
        try:
            with open(self.filename, 'w', newline='', encoding='utf-8') as f:
                # 动态获取所有字段名，确保灵活性
                if self.data:
                    fieldnames = set()
                    for row in self.data:
                        fieldnames.update(row.keys())
                    fieldnames = sorted(list(fieldnames)) # 排序以便于阅读
                else:
                    fieldnames = ['timestamp', 'class', 'name', '猜铁_success', '猜铁_attempts', '国景_success', '国景_attempts', '填国_success', '填国_attempts']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for entry in self.data:
                    writer.writerow(entry)
        except Exception as e:
            print(f"Error saving leaderboard: {e}")

    def _find_entry(self, class_name, student_name):
        """辅助方法：查找或创建玩家记录"""
        for entry in self.data:
            if entry['class'] == class_name and entry['name'] == student_name:
                return entry
        # 如果未找到，创建新记录
        new_entry = {'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'class': class_name, 'name': student_name}
        self.data.append(new_entry)
        return new_entry

    def add_score(self, class_name, student_name, module_name, success, attempts, answer=None):
        """添加或更新特定模块的成绩到排行榜"""
        entry = self._find_entry(class_name, student_name)

        success_key = f"{module_name}_success"
        attempts_key = f"{module_name}_attempts"

        # 只有在成功时才更新，或者如果之前未记录过该模块
        if success or (success_key not in entry):
            entry[success_key] = '1' if success else '0'
            entry[attempts_key] = str(attempts) if success else 'N/A' # 未通过则记录N/A或保持原值
            # 更新时间戳
            entry['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.save()

    def update_score(self, class_name, student_name, module_name, success, attempts):
        """
        预留接口：用于其他模块修改或添加成绩。
        例如，可以在“国景”或“填国”模块完成后调用此方法。
        """
        self.add_score(class_name, student_name, module_name, success, attempts)

    def get_all_scores(self):
        """获取所有成绩，按通过题数降序，总尝试次数升序排序"""
        def calculate_score(entry):
            # 计算通过题数和总尝试次数
            passed_modules = 0
            total_attempts = 0
            for module in ['猜铁', '国景', '填国']:
                success_key = f"{module}_success"
                attempts_key = f"{module}_attempts"
                if entry.get(success_key) == '1':
                    passed_modules += 1
                    try:
                        # 尝试将 attempts 转换为整数，只累加成功模块的尝试次数
                        total_attempts += int(entry.get(attempts_key, 0))
                    except ValueError:
                        # 如果 attempts 不是数字（例如 'N/A'），则跳过
                        pass
            return passed_modules, total_attempts

        # 按规则排序：先按通过题数降序，再按总尝试次数升序
        sorted_data = sorted(self.data, key=lambda x: calculate_score(x)[0], reverse=True)
        sorted_data = sorted(self.data, key=lambda x: (-calculate_score(x)[0], calculate_score(x)[1]))
        return sorted_data

    def get_paginated_scores(self, page, per_page=10):
        """获取分页后的排行榜数据"""
        all_scores = self.get_all_scores()
        start = (page - 1) * per_page
        end = start + per_page
        paginated_scores = all_scores[start:end]
        total_pages = (len(all_scores) + per_page - 1) // per_page  # 向上取整计算总页数
        return paginated_scores, total_pages

# --- 上海地铁图类 ---
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
            with open('data/ShortestRoute.csv', 'r', encoding='utf-8') as f:
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
            print("Warning: data/ShortestRoute.csv not found. Calculating distances will fail.")
        except Exception as e:
            print(f"Error loading shortest routes: {e}")

        # 加载最少换乘次数
        try:
            with open('data/MinimumChange.csv', 'r', encoding='utf-8') as f:
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
            print("Warning: data/MinimumChange.csv not found. Calculating transfers will fail.")
        except Exception as e:
            print(f"Error loading minimum changes: {e}")


    def load_stations(self):
        """加载上海地铁站点数据"""
        try:
            with open('data/StationInfo.csv', 'r', encoding='utf-8') as f:
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
                        "opening_year": opening_year
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
                            "line": line
                        }
        except FileNotFoundError:
            print("Error: data/StationInfo.csv not found.")
        except Exception as e:
            print(f"Error loading station info: {e}")
    
    def calculate_min_stations(self, start_station: str, end_station: str) -> int:
        """计算最小站数 - 从预加载的CSV数据中获取"""
        if start_station in self.shortest_routes and end_station in self.shortest_routes[start_station]:
            return self.shortest_routes[start_station][end_station]
        else:
            return 100

    def calculate_min_transfers(self, start_station: str, end_station: str) -> int:
        """计算最小换乘次数 - 从预加载的CSV数据中获取"""
        if start_station in self.minimum_changes and end_station in self.minimum_changes[start_station]:
            return self.minimum_changes[start_station][end_station]
        else:
            return 10


    def get_all_stations(self) -> List[str]:
        """获取所有站点列表"""
        return sorted(list(self.stations.keys()))
    
    def get_station_info(self, station_name: str) -> Dict:
        """获取站点信息"""
        return self.stations.get(station_name, {})

# 初始化地铁图
metro_graph = ShanghaiMetroGraph()
# 初始化排行榜
leaderboard = Leaderboard()

try:
    from calculator import bearing, dist, latlongbrng
except ImportError:
    print("Warning: calculator.py not found. Using mock functions.")
    # Mock functions for calculator if file is missing
    def bearing(latlong1, latlong2):
        return 0.0
    def dist(latlong1, latlong2):
        return 0.0
    def latlongbrng(latlong1, latlong2):
        return 0.0

try:
    from data import nation_template
except ImportError:
    print("Warning: data.py not found. Using mock data.")
    # Mock data for nation_template if file is missing
    nation_template = [
        [["TestCountry1"], ["测试国家1"], ["テストカントリー1"], [30.0, 120.0]],
        [["TestCountry2"], ["测试国家2"], ["テストカントリー2"], [35.0, 130.0]],
    ]

try:
    from problems import problem_set
except ImportError:
    print("Warning: problems.py not found. Using mock data.")
    # Mock data for problem_set if file is missing
    problem_set = [
        [0, 'test_image.jpg', [30.0, 120.0]], # 使用第一个测试国家的索引
    ]
    
try:
    from problems_fill_country import fill_guo_problems
except ImportError:
    print("Warning: problems_fill_country.py not found. Using mock data.")
    fill_guo_problems = []
    
def build_nation_lookup():
    """构建国家名称查找字典 {name.lower(): {'zh_name': str, 'coords': list}}"""
    lookup = {}
    for nation_info in nation_template:
        if nation_info and len(nation_info) > 3:
            # 假设 nation_info 格式为 [ [en_names], [zh_names], [other_names], [lat, lon] ]
            # 将所有名称列表合并
            all_names = []
            for name_list in nation_info[:2]: # 取前三个列表（英文、中文、其他）
                if isinstance(name_list, list):
                    all_names.extend(name_list)
            coords = nation_info[3]

            # 获取首选中文名（通常是列表第一个）
            zh_name = nation_info[1][0] if nation_info[1] else "未知国家"

            # 为每个名称创建映射
            for name in all_names:
                if isinstance(name, str) and name.strip():
                    lookup[name.lower()] = {'zh_name': zh_name, 'coords': coords}
    # print("Debug: Nation lookup keys (first 10):", list(lookup.keys())[:10])
    # print("Debug: Example lookup entry for 'china':", lookup.get('china'))
    return lookup

# 构建查找字典
nation_lookup = build_nation_lookup()

def validate_fill_guo_grid(problem_id, grid):
    """
    验证填国网格是否满足所有条件。
    grid: 3x3 列表，包含国家名称或 None
    constraints: 预留接口，当前未使用
    solution: 预留接口，当前未使用
    返回: (is_finished: bool, is_valid: bool, error_message: str or None)
           is_finished: 网格是否已填满且正确
           is_valid: 当前网格状态（填满时）是否有效（满足条件），或（未填满时）是否不违反唯一性
           error_message: 错误信息
    """
    print(grid)
    flat_grid = []
    # 检查国家是否唯一
    for i in range(0, 3):
        for j in range(0, 3):
            if grid[i][j] is not None:
                flat_grid.append(grid[i][j])
    
    # 检查唯一性
    if len(set(flat_grid)) != len(flat_grid):
        return False, False, "国家不能重复，请确保九个格子的国家都不相同。" # 未填满，无效，有错误
    
    cell_options = fill_guo_problems[problem_id]["cell_options"]
    flag = 0 
    for i in range(0,3):
        for j in range(0,3):
            if grid[i][j] is None:
                continue
            temp_set = f"{i},{j}"
            print(cell_options[temp_set])
            if cell_options[temp_set].count(grid[i][j]) < 1:
                flag = 1
                break
        if flag == 1:
            break # 提前退出外层循环
    
    # 检查是否已填满
    if len(flat_grid) == 9:
        if flag == 0:
            # 填满了，且满足条件
            return True, True, None # is_finished=True, is_valid=True
        else:
            # 填满了，但不满足条件
            return True, False, "网格内容不符合题目要求。" # is_finished=True, is_valid=False
    else:
        # 未填满
        if flag == 0:
            # 未填满，但目前有效（满足唯一性和选项限制）
            return False, True, None # is_finished=False, is_valid=True
        else:
            # 未填满，且已违反条件（这在当前逻辑下不应该发生，因为只有填入时才检查）
            # 为了健壮性，可以返回无效状态
            return False, False, "网格内容不符合题目要求。" # is_finished=False, is_valid=False


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
        # 随机选择答案 (仅在 session 中没有答案时)
        if 'answer' not in session:
            all_stations = metro_graph.get_all_stations()
            answer = random.choice(all_stations)
            session['answer'] = answer
            session['guesses'] = [] # 初始化猜测列表
            session['attempts'] = 0
            session['game_over'] = False
            print(f"猜铁游戏开始 - 新答案: {answer}")
        else:
            print(f"猜铁游戏继续 - 答案: {session['answer']}, 已有猜测: {len(session['guesses'])}")
        
        session['game_type'] = 'metro_guess'
        session['max_attempts'] = 6
        
        return render_template('metro_game.html',
                             stations=metro_graph.get_all_stations(),
                             initial_guesses=session.get('guesses', [])) # 传递历史猜测
        
    elif game_type == 'guo_jing':
        # ... (其他代码保持不变) ...
        # 随机选择一个题目
        if not problem_set:
            return "没有可用的题目", 500
        
        problem = random.choice(problem_set)
        nation_index = problem[0]
        image_filename = problem[1]
        target_coords = problem[2]

        # 获取国家名称
        if 0 <= nation_index < len(nation_template):
            nation_info = nation_template[nation_index]
            nation_names = nation_info[0] # 使用英文名作为标准答案
            correct_nation_name = nation_names[0] if nation_names else "Unknown"
            correct_nation_zh_name = nation_info[1][0] if nation_info[1] else "未知国家" # 获取中文名用于显示
        else:
            return "题目数据错误", 500

        session['game_type'] = 'guo_jing'
        session['answer_nation_index'] = nation_index
        session['answer_nation_name'] = correct_nation_name
        session['answer_nation_zh_name'] = correct_nation_zh_name # 存储中文名
        session['answer_coords'] = target_coords
        session['image_filename'] = image_filename
        session['guesses'] = []
        session['attempts'] = 0
        session['max_attempts'] = 6
        session['game_over'] = False

        print(f"国景游戏开始 - 答案: {correct_nation_name} ({correct_nation_zh_name}), 坐标: {target_coords}, 图片: {image_filename}")

        # --- 修改这里 ---
        # 获取所有国家的**所有可能名称**列表用于前端选择和搜索
        all_possible_names = []
        for nation_info in nation_template:
            if nation_info and len(nation_info) > 3:
                # 将所有名称列表合并
                for name_list in nation_info[:3]: # 取前三个列表（英文、中文、其他）
                    if isinstance(name_list, list):
                        all_possible_names.extend(name_list)
        
        # 去重并过滤空字符串
        all_possible_names = list(set(name for name in all_possible_names if name.strip()))
        
        # --- 传递所有可能的名称列表 ---
        return render_template('guo_jing_game.html',
                               nations=all_possible_names, # 传递所有可能名称列表
                               image_filename=image_filename)
    
    elif game_type == 'tian_guo':
        # ... (其他代码保持不变) ...
        if not fill_guo_problems:
            return "没有可用的题目", 500

        problem_index = session.get('fill_guo_problem_index', 0)
        if problem_index >= len(fill_guo_problems):
             if problem_index == len(fill_guo_problems): # 刚完成最后一题
                 return redirect('/menu')
             else:
                 return "题目数据错误或索引超出范围", 500

        problem = fill_guo_problems[problem_index]
        
        all_possible_names = []
        for nation_info in nation_template:
            if nation_info and len(nation_info) > 3:
                for name_list in nation_info[:2]:
                    if isinstance(name_list, list):
                        all_possible_names.extend(name_list)
        
        all_possible_names = list(set(name for name in all_possible_names if name.strip()))

        session['game_type'] = 'tian_guo'
        if 'fill_guo_problem_index' not in session:
            session['fill_guo_problem_index'] = problem_index
        session['fill_guo_problem'] = problem
        if 'fill_guo_grid' not in session:
            session['fill_guo_grid'] = [[None for _ in range(3)] for _ in range(3)]
        if 'fill_guo_errors' not in session:
            session['fill_guo_errors'] = 0
        if 'fill_guo_max_errors' not in session:
            session['fill_guo_max_errors'] = [5, 8, 10, 15, 20][problem_index]
        if 'fill_guo_game_over' not in session:
            session['fill_guo_game_over'] = False
        if 'fill_guo_success' not in session:
            session['fill_guo_success'] = False

        print(f"填国游戏加载 - 题目 {problem_index + 1}, 最大错误次数: {session['fill_guo_max_errors']}")

        return render_template('tian_guo_game.html',
                               nations=all_possible_names,
                               problem=problem)
    
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
        # 游戏成功，记录“猜铁”模块成绩到排行榜
        class_name = session.get('class', 'Unknown Class')
        student_name = session.get('name', 'Anonymous')
        leaderboard.add_score(class_name, student_name, '猜铁', success=True, attempts=attempts, answer=answer)
    elif attempts >= session.get('max_attempts', 6):
        game_over = True
        session['game_over'] = True
        # 游戏失败，也记录“猜铁”模块成绩（未通过）
        class_name = session.get('class', 'Unknown Class')
        student_name = session.get('name', 'Anonymous')
        leaderboard.add_score(class_name, student_name, '猜铁', success=False, attempts=attempts, answer=answer)

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

# app.py (在 submit_guess_guo_jing 函数之前或其他合适的位置添加这个新函数)

def degrees_to_chinese_direction(bearing_degrees):
    """将度数转换为中文方向描述"""
    if bearing_degrees < 0:
        bearing_degrees += 360
    bearing_degrees %= 360

    directions = ['⬆️', '↗️', '➡️', '↘️', '⬇️', '↙️', '⬅️', '↖️']
    index = round(bearing_degrees / (360 / len(directions))) % len(directions)
    return directions[index]

# ... (其他 app.py 代码保持不变) ...

@app.route('/submit_guess_guo_jing', methods=['POST'])
def submit_guess_guo_jing():
    """处理国景模块的猜测"""
    if session.get('game_over'):
        return jsonify({'game_over': True})

    guess_input = request.json.get('guess') # 用户输入的可能是中文、英文或简称
    answer_nation_name = session.get('answer_nation_name')
    answer_nation_zh_name = session.get('answer_nation_zh_name')
    answer_coords = session.get('answer_coords')

    if not guess_input or not answer_nation_name or not answer_coords:
        return jsonify({'error': '数据错误'})

    # 在 nation_lookup 中查找猜测的国家信息 (现在查找的是输入的原始字符串)
    lookup_result = nation_lookup.get(guess_input.lower())
    if not lookup_result:
        return jsonify({'error': f'猜测的国家不存在: {guess_input}'})

    # 获取国家的中文全称和坐标
    guess_nation_zh_name = lookup_result['zh_name']
    guess_coords = lookup_result['coords']

    # 计算距离和方向
    distance = dist(guess_coords, answer_coords)
    bearing_angle_raw = bearing(guess_coords, answer_coords) # 获取度数值
    latlongbrng_raw = latlongbrng(guess_coords, answer_coords)

    # 确保 bearing_angle 是数值类型
    try:
        bearing_angle = float(bearing_angle_raw)
    except (ValueError, TypeError) as e:
        print(f"Error converting bearing angle '{bearing_angle_raw}' to float: {e}")
        # 设置一个默认值或返回错误
        return jsonify({'error': f'计算方向时出错: {e}'})
    
    # 确保 bearing_angle 是数值类型
    try:
        latlongbrng_angle = float(latlongbrng_raw)
    except (ValueError, TypeError) as e:
        print(f"Error converting bearing angle '{latlongbrng_raw}' to float: {e}")
        # 设置一个默认值或返回错误
        return jsonify({'error': f'计算方向时出错: {e}'})


    direction1 = degrees_to_chinese_direction(bearing_angle) # 使用新的中文方向转换函数\
    direction2 = degrees_to_chinese_direction(latlongbrng_angle)

    # 创建结果 (显示中文全称)
    result = {
        'guess': guess_nation_zh_name, # 显示中文全称
        'distance': round(distance, 2),
        'direction1': direction1,
        'direction2': direction2,
        'bearing': round(bearing_angle, 2), # 原始角度，用于前端可能的更复杂处理
        'is_correct': guess_nation_zh_name == answer_nation_zh_name # 比较也用中文名
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
    if guess_nation_zh_name == answer_nation_zh_name: # 结束条件也用中文名
        game_over = True
        session['game_over'] = True
        # 游戏成功，记录“国景”模块成绩到排行榜 (记录中文名)
        class_name = session.get('class', 'Unknown Class')
        student_name = session.get('name', 'Anonymous')
        leaderboard.add_score(class_name, student_name, '国景', success=True, attempts=attempts, answer=answer_nation_zh_name)
    elif attempts >= session.get('max_attempts', 6):
        game_over = True
        session['game_over'] = True
        # 游戏失败，也记录“国景”模块成绩（未通过）(记录中文名)
        class_name = session.get('class', 'Unknown Class')
        student_name = session.get('name', 'Anonymous')
        leaderboard.add_score(class_name, student_name, '国景', success=False, attempts=attempts, answer=answer_nation_zh_name)

    session.modified = True

    response_data = {
        'result': result,
        'attempts_left': session.get('max_attempts', 6) - attempts,
        'game_over': game_over
    }

    # 只有在游戏结束且没有猜对的情况下才返回答案 (返回中文名)
    if game_over and guess_nation_zh_name != answer_nation_zh_name:
        response_data['answer'] = answer_nation_zh_name

    return jsonify(response_data)

@app.route('/fill_guo_select_nation', methods=['POST'])
def fill_guo_select_nation():
    """处理填国模块选择国家的请求"""
    if session.get('fill_guo_game_over'):
        return jsonify({'game_over': True})

    data = request.json
    row = data.get('row')
    col = data.get('col')
    nation_name_input = data.get('nation') # 用户输入的名称（可能是英文、中文、简称等）

    if row is None or col is None or not nation_name_input:
        return jsonify({'error': '数据错误'})

    # --- 修改：通过 nation_lookup 获取中文全称 ---
    lookup_result = nation_lookup.get(nation_name_input.lower())
    if not lookup_result:
        return jsonify({'error': f'选择的国家不存在: {nation_name_input}'})

    nation_name_zh = lookup_result['zh_name'] # 获取中文全称

    # 获取当前网格
    grid = session.get('fill_guo_grid', [[None for _ in range(3)] for _ in range(3)])
    problem_id = session.get('fill_guo_problem_index')
    cell_options = fill_guo_problems[problem_id]["cell_options"]

    # --- 新增验证：检查新选择的国家是否违反规则 ---
    # 1. 检查是否与网格中已有的国家重复 (使用中文全称)
    flat_grid = [cell for r_row in grid for cell in r_row]
    if nation_name_zh in flat_grid:
        # 选择的国家重复了
        errors = session.get('fill_guo_errors', 0) + 1
        session['fill_guo_errors'] = errors
        game_over = False
        if errors >= session.get('fill_guo_max_errors', 5):
            game_over = True
            session['fill_guo_game_over'] = True
            # 记录失败成绩到排行榜
            class_name = session.get('class', 'Unknown Class')
            student_name = session.get('name', 'Anonymous')
            problem_index = session.get('fill_guo_problem_index', 0)
            module_name = f"填国{problem_index + 1}"
            leaderboard.add_score(class_name, student_name, module_name, success=False, attempts=errors, answer="N/A")
        return jsonify({
            'success': False, # 前端请求失败（因为国家重复）
            'grid': grid, # 返回未修改的网格
            'error_message': "选择的国家已存在于网格中，请选择其他国家。",
            'errors_left': session.get('fill_guo_max_errors', 5) - errors,
            'game_over': game_over,
            'success': False
        })

    # 2. 检查是否在该格子的可选项中 (使用中文全称)
    temp_set = f"{row},{col}"
    possible_nations = cell_options.get(temp_set, [])
    if nation_name_zh not in possible_nations:
        # 选择的国家不在该格子的可选项中
        errors = session.get('fill_guo_errors', 0) + 1
        session['fill_guo_errors'] = errors
        game_over = False
        if errors >= session.get('fill_guo_max_errors', 5):
            game_over = True
            session['fill_guo_game_over'] = True
            # 记录失败成绩到排行榜
            class_name = session.get('class', 'Unknown Class')
            student_name = session.get('name', 'Anonymous')
            problem_index = session.get('fill_guo_problem_index', 0)
            module_name = f"填国{problem_index + 1}"
            leaderboard.add_score(class_name, student_name, module_name, success=False, attempts=errors, answer="N/A")
        return jsonify({
            'success': False, # 前端请求失败（因为国家不在选项中）
            'grid': grid, # 返回未修改的网格
            'error_message': "选择的国家不符合该格子的条件。",
            'errors_left': session.get('fill_guo_max_errors', 5) - errors,
            'game_over': game_over,
            'success': False
        })

    # 如果新国家符合要求，先更新网格 (使用中文全称)
    grid[row][col] = nation_name_zh
    session['fill_guo_grid'] = grid

    # 验证更新后的网格状态 (使用中文全称)
    is_finished, is_valid, error_msg = validate_fill_guo_grid(problem_id, grid)

    if is_finished and is_valid:
        # 成功：网格填满且有效
        session['fill_guo_success'] = True
        # --- 修改：记录成绩到排行榜 ---
        class_name = session.get('class', 'Unknown Class')
        student_name = session.get('name', 'Anonymous')
        problem_index = session.get('fill_guo_problem_index', 0)
        module_name = f"填国{problem_index + 1}"
        errors = session.get('fill_guo_errors', 0)
        leaderboard.add_score(class_name, student_name, module_name, success=True, attempts=errors, answer="N/A") # 尝试次数用错误次数表示

        # --- 新增：检查是否还有下一题 ---
        next_problem_index = problem_index + 1
        if next_problem_index < len(fill_guo_problems):
            # 有下一题，准备加载下一题
            next_problem = fill_guo_problems[next_problem_index]
            all_possible_names = []
            for nation_info in nation_template:
                if nation_info and len(nation_info) > 3:
                    for name_list in nation_info[:2]: # 取前两个列表（英文、中文）
                        if isinstance(name_list, list):
                            all_possible_names.extend(name_list)
            all_possible_names = list(set(name for name in all_possible_names if name.strip()))

            session['fill_guo_problem_index'] = next_problem_index
            session['fill_guo_problem'] = next_problem
            session['fill_guo_grid'] = [[None for _ in range(3)] for _ in range(3)] # 初始化空网格
            session['fill_guo_errors'] = 0 # 重置错误次数
            session['fill_guo_max_errors'] = [5, 8, 10, 15, 20][next_problem_index] # 根据题目设置最大错误次数
            session['fill_guo_game_over'] = False
            session['fill_guo_success'] = False # 重置成功状态

            print(f"填国游戏 - 完成第 {problem_index + 1} 题，进入第 {next_problem_index + 1} 题, 最大错误次数: {session['fill_guo_max_errors']}")

            # 返回成功信息，并标记需要加载新题目
            return jsonify({
                'success': True,
                'message': f'恭喜，你完成了第 {problem_index + 1} 题！',
                'grid': session['fill_guo_grid'], # 返回新题目的空网格
                'errors_left': session['fill_guo_max_errors'], # 返回新题目的最大错误次数
                'problem_index': next_problem_index, # 返回新题目的索引
                'problem': next_problem, # 返回新题目的数据 (如果前端需要)
                'load_next': True # 标记前端需要加载新题目
            })
        else:
            # 没有下一题了，游戏结束
            session['fill_guo_game_over'] = True
            return jsonify({
                'success': True,
                'message': '恭喜，你完成了所有填国题目！',
                'grid': grid,
                'game_over': True,
                'success': True # 全部完成
            })

    # 如果网格未完成 或者 网格完成但无效（理论上不应该发生，因为唯一性和选项检查在前）
    # 但在当前逻辑下，`validate_fill_guo_grid` 只检查唯一性和选项池，不检查是否填满
    # 所以 `is_valid` 为 False 只可能是因为 `validate_fill_guo_grid` 内部有其他未实现的检查
    # 如果 `is_valid` 为 False，说明填入后违反了某些规则，需要增加错误次数
    errors = session.get('fill_guo_errors', 0)
    if not is_valid:
        errors += 1
        session['fill_guo_errors'] = errors # 更新session中的错误次数
        # 如果是无效状态，回退网格
        grid[row][col] = None
        session['fill_guo_grid'] = grid

    game_over = False
    if errors >= session.get('fill_guo_max_errors', 5):
        game_over = True
        session['fill_guo_game_over'] = True
        # 记录失败成绩到排行榜
        class_name = session.get('class', 'Unknown Class')
        student_name = session.get('name', 'Anonymous')
        problem_index = session.get('fill_guo_problem_index', 0)
        module_name = f"填国{problem_index + 1}"
        leaderboard.add_score(class_name, student_name, module_name, success=False, attempts=errors, answer="N/A")

    return jsonify({
        'success': True, # 前端请求本身是成功的（即使国家不符合要求）
        'grid': grid, # 返回可能更新或回退后的网格
        'error_message': error_msg, # 如果是无效状态，返回错误信息
        'errors_left': session.get('fill_guo_max_errors', 5) - errors, # 返回剩余次数
        'game_over': game_over,
        'success': False # 未成功完成整个谜题
    })
    
@app.route('/fill_guo_reset_grid', methods=['POST'])
def fill_guo_reset_grid():
    """重置填国网格"""
    if session.get('fill_guo_game_over'):
        return jsonify({'error': '游戏已结束，无法重置'})

    session['fill_guo_grid'] = [[None for _ in range(3)] for _ in range(3)]
    # --- 移除这一行：session['fill_guo_errors'] = 0 ---
    # 错误次数不清空
    return jsonify({'grid': session['fill_guo_grid']})

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

@app.route('/leaderboard')
def show_leaderboard():
    """显示排行榜"""
    page = int(request.args.get('page', 1))
    scores, total_pages = leaderboard.get_paginated_scores(page, per_page=10)
    return render_template('leaderboard.html', scores=scores, page=page, total_pages=total_pages)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)