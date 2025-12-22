from flask import Flask, render_template, request, jsonify, session, redirect
import json
import random
from datetime import datetime
from collections import deque, defaultdict
import heapq
from typing import List, Dict, Tuple, Set
import pandas as pd

app = Flask(__name__)
app.secret_key = 'shanghai-metro-guess-secret-key-2024'
StationInfo = pd.read_csv('./data/StationInfo.csv', encoding='utf-8')
ShortestRoute = pd.read_csv('./data/ShortestRoute.csv', encoding='utf-8')
MinimumChange = pd.read_csv('./data/MinimumChange.csv', encoding='utf-8')

class ShanghaiMetroGraph:
    """上海地铁网络图"""
    def __init__(self):
        # 初始化数据结构
        self.stations = {}  # 站点信息
        self.lines = {}     # 线路信息
        self.graph = defaultdict(list)  # 邻接表表示的地铁网络
        self.station_lines = defaultdict(set)  # 站点对应的线路
        self.station_nodes = {}  # 站点节点映射（支持同站不同线）
        
    
    def load_stations(self):
        """加载站点数据"""
        try:
            print(f"StationInfo shape: {StationInfo.shape}")
            print(f"StationInfo columns: {list(StationInfo.columns)}")
            
            if len(StationInfo) == 0:
                raise ValueError("StationInfo DataFrame is empty")
            
            successful_loads = 0
            
            for idx in range(len(StationInfo)):
                try:
                    row = StationInfo.iloc[idx]
                    
                    # 检查站名是否存在且不为空
                    station_name = row["站名"]
                    if pd.isna(station_name) or str(station_name).strip() == '':
                        continue
                    
                    name = str(station_name).strip()
                    
                    # 收集线路信息
                    Line = []
                    for col_num in range(1, 6):  # 线路1-5
                        line_col = f"线路{col_num}" if col_num > 1 else "线路1"
                        if line_col in StationInfo.columns:
                            line_val = row[line_col]
                            if pd.notna(line_val) and str(line_val).strip() != '':
                                Line.append(str(line_val).strip())
                    
                    # 获取其他信息
                    district = str(row["区县"]).strip() if pd.notna(row["区县"]) else ""
                    open_year = str(row['开通年份']).strip() if pd.notna(row['开通年份']) else "0"
                    
                    # 存储站点信息
                    self.stations[name] = {
                        "district": district,
                        "lines": Line,
                        "opening_year": open_year
                    }
                    successful_loads += 1
                    
                except Exception as e:
                    print(f"Error processing row {idx}: {e}")
                    continue
            
            print(f"成功加载 {successful_loads} 个站点")
            if successful_loads == 0:
                print("警告：没有成功加载任何站点数据")
                
        except Exception as e:
            print(f"加载站点数据时发生严重错误: {e}")
            raise
    # 
        
        # 初始化数据
        self.load_stations()
        # self.build_graph()
    
    # def load_stations(self):
    #     """加载上海地铁站点数据"""
    #     # 上海地铁站点数据（截至2024年，约400个站点中的关键站点）
    #     
        
    #     # 处理站点数据
    #     for station in station_data:
    #         name = station["name"]
    #         lines = station["lines"]  # 已经是"X号线"格式
            
    #         # 存储站点信息
    #         self.stations[name] = {
    #             "district": station["district"],
    #             "lines": lines,
    #             "opening_year": station["opening_year"],
    #             "position": {"x": station["x"], "y": station["y"]}
    #         }
            
    #         # 存储站点线路关系
    #         for line in lines:
    #             self.station_lines[name].add(line)
    #             if line not in self.lines:
    #                 self.lines[line] = []
    #             if name not in self.lines[line]:
    #                 self.lines[line].append(name)
                
    #         # 创建站点节点（考虑同站不同线的情况）
    #         for line in lines:
    #             node_id = f"{name}_{line}"
    #             self.station_nodes[node_id] = {
    #                 "station_name": name,
    #                 "line": line,
    #                 "position": {"x": station["x"], "y": station["y"]}
    #             }
    
    # def build_graph(self):
    #     """构建地铁网络图"""
    #     # 构建每条线路上的连接
    #     for line, stations in self.lines.items():
    #         for i in range(len(stations) - 1):
    #             station_a = stations[i]
    #             station_b = stations[i + 1]
                
    #             # 创建节点ID
    #             node_a = f"{station_a}_{line}"
    #             node_b = f"{station_b}_{line}"
                
    #             # 添加双向连接（权重为1，表示一站）
    #             self.graph[node_a].append((node_b, 1))
    #             self.graph[node_b].append((node_a, 1))
        
    #     # 添加换乘站内部的连接（同站不同线之间的换乘通道）
    #     station_groups = defaultdict(list)
        
    #     for node_id, info in self.station_nodes.items():
    #         station_name = info["station_name"]
    #         station_groups[station_name].append(node_id)
        
    #     # 对于每个换乘站，连接所有线路节点（换乘通道，权重为0.5表示换乘时间）
    #     for station_name, nodes in station_groups.items():
    #         if len(nodes) > 1:  # 换乘站
    #             for i in range(len(nodes)):
    #                 for j in range(i + 1, len(nodes)):
    #                     self.graph[nodes[i]].append((nodes[j], 0.5))  # 换乘时间
    #                     self.graph[nodes[j]].append((nodes[i], 0.5))
    
    # def find_shortest_path(self, start_station: str, end_station: str) -> Tuple[int, int, List[str]]:
    #     """
    #     使用Dijkstra算法计算最短路径
        
    #     返回: (最小站数, 最小换乘次数, 路径节点列表)
    #     """
    #     if start_station == end_station:
    #         return 0, 0, []
        
    #     # 获取起点和终点的所有节点（不同线路）
    #     start_nodes = [node for node in self.station_nodes if node.startswith(start_station + "_")]
    #     end_nodes = [node for node in self.station_nodes if node.startswith(end_station + "_")]
        
    #     if not start_nodes or not end_nodes:
    #         return float('inf'), float('inf'), []
        
    #     # Dijkstra算法
    #     dist = {}
    #     prev = {}
    #     visited = set()
    #     pq = []
        
    #     # 初始化
    #     for node in start_nodes:
    #         dist[node] = 0
    #         heapq.heappush(pq, (0, node))
        
    #     # Dijkstra主循环
    #     while pq:
    #         current_dist, current_node = heapq.heappop(pq)
            
    #         if current_node in visited:
    #             continue
    #         visited.add(current_node)
            
    #         # 如果到达任一终点节点
    #         current_station = current_node.split("_")[0]
    #         if current_station == end_station:
    #             # 重建路径
    #             path = []
    #             node = current_node
    #             while node is not None:
    #                 path.append(node)
    #                 node = prev.get(node)
    #             path.reverse()
                
    #             # 计算站数和换乘次数
    #             stations_visited = set()
    #             transfers = 0
    #             current_line = None
                
    #             for node in path:
    #                 station_name = node.split("_")[0]
    #                 line_name = node.split("_")[1]
    #                 stations_visited.add(station_name)
                    
    #                 if current_line is not None and current_line != line_name:
    #                     transfers += 1
    #                 current_line = line_name
                
    #             # 站数是访问的唯一站点数减1（起点不计入）
    #             station_count = len(stations_visited) - 1
                
    #             return station_count, transfers, path
            
    #         # 遍历邻居
    #         for neighbor, weight in self.graph[current_node]:
    #             if neighbor in visited:
    #                 continue
                
    #             new_dist = current_dist + weight
    #             if neighbor not in dist or new_dist < dist[neighbor]:
    #                 dist[neighbor] = new_dist
    #                 prev[neighbor] = current_node
    #                 heapq.heappush(pq, (new_dist, neighbor))
        
    #     # 没有找到路径
    #     return float('inf'), float('inf'), []
    
    def calculate_min_stations(self, start_station: str, end_station: str) -> int:
        """计算最小站数"""
        filtered_df = ShortestRoute[ShortestRoute["站名"] == start_station]
        if filtered_df.empty:
            return int('inf')  # 或其他默认值
        return int(filtered_df.iloc[0][end_station])

    def calculate_min_transfers(self, start_station: str, end_station: str) -> int:
        """计算最小换乘次数"""
        filtered_df = MinimumChange[MinimumChange["站名"] == start_station]
        if filtered_df.empty:
            return int('inf')  # 或其他默认值
        return int(filtered_df.iloc[0][end_station])
    
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
        if not all_stations:
            print("错误：没有加载到任何站点数据")
            return "没有可用的站点数据，请检查数据文件", 500
        
        print(f"可用站点数量: {len(all_stations)}")
        
        if len(all_stations) == 0:
            return "没有可用的站点数据", 500
        
        answer = random.choice(all_stations)
        
        session['game_type'] = 'metro_guess'
        session['answer'] = answer
        session['guesses'] = []
        session['attempts'] = 0
        session['max_attempts'] = 6
        session['game_over'] = False
        
        print(f"游戏开始 - 答案: {answer}")
        
        return render_template('metro_game.html', stations=all_stations)
    
    return redirect('/menu')

@app.route('/submit_guess', methods=['POST'])
def submit_guess():
    # """处理猜测"""
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
    
    # 计算最小站数和换乘次数
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
    info = StationInfo[StationInfo['站名']==station_name]
    if info:
        return jsonify({'success': True, 'info': info})
    return jsonify({'success': False, 'error': '站点不存在'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)