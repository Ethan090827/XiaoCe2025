from flask import Flask, render_template, request, jsonify, session, redirect
import json
import random
from datetime import datetime
from collections import deque, defaultdict
import heapq
from typing import List, Dict, Tuple, Set

app = Flask(__name__)
app.secret_key = 'shanghai-metro-guess-secret-key-2024'

class ShanghaiMetroGraph:
    """上海地铁网络图"""
    
    def __init__(self):
        # 初始化数据结构
        self.stations = {}  # 站点信息
        self.lines = {}     # 线路信息
        self.graph = defaultdict(list)  # 邻接表表示的地铁网络
        self.station_lines = defaultdict(set)  # 站点对应的线路
        self.station_nodes = {}  # 站点节点映射（支持同站不同线）
        
        # 初始化数据
        self.load_stations()
        self.build_graph()
    
    def load_stations(self):
        """加载上海地铁站点数据"""
        # 上海地铁站点数据（截至2024年，约400个站点中的关键站点）
        station_data = [
            # 1号线
            {"name": "莘庄", "lines": ["1号线"], "district": "闵行区", "opening_year": 1996, "x": 10, "y": 100},
            {"name": "外环路", "lines": ["1号线"], "district": "闵行区", "opening_year": 1996, "x": 20, "y": 100},
            {"name": "莲花路", "lines": ["1号线"], "district": "闵行区", "opening_year": 1996, "x": 30, "y": 100},
            {"name": "锦江乐园", "lines": ["1号线"], "district": "闵行区", "opening_year": 1996, "x": 40, "y": 100},
            {"name": "上海南站", "lines": ["1号线", "3号线", "15号线"], "district": "徐汇区", "opening_year": 1996, "x": 50, "y": 100},
            {"name": "漕宝路", "lines": ["1号线", "12号线"], "district": "徐汇区", "opening_year": 1996, "x": 60, "y": 100},
            {"name": "上海体育馆", "lines": ["1号线", "4号线"], "district": "徐汇区", "opening_year": 1996, "x": 70, "y": 100},
            {"name": "徐家汇", "lines": ["1号线", "9号线", "11号线"], "district": "徐汇区", "opening_year": 1996, "x": 80, "y": 100},
            {"name": "衡山路", "lines": ["1号线"], "district": "徐汇区", "opening_year": 1996, "x": 90, "y": 100},
            {"name": "常熟路", "lines": ["1号线", "7号线"], "district": "徐汇区", "opening_year": 1996, "x": 100, "y": 100},
            {"name": "陕西南路", "lines": ["1号线", "10号线", "12号线"], "district": "黄浦区", "opening_year": 1996, "x": 110, "y": 100},
            {"name": "黄陂南路", "lines": ["1号线"], "district": "黄浦区", "opening_year": 1996, "x": 120, "y": 100},
            {"name": "人民广场", "lines": ["1号线", "2号线", "8号线"], "district": "黄浦区", "opening_year": 1995, "x": 130, "y": 100},
            {"name": "新闸路", "lines": ["1号线"], "district": "静安区", "opening_year": 1996, "x": 140, "y": 100},
            {"name": "汉中路", "lines": ["1号线", "12号线", "13号线"], "district": "静安区", "opening_year": 1996, "x": 150, "y": 100},
            {"name": "上海火车站", "lines": ["1号线", "3号线", "4号线"], "district": "静安区", "opening_year": 1996, "x": 160, "y": 100},
            {"name": "中山北路", "lines": ["1号线"], "district": "静安区", "opening_year": 1996, "x": 170, "y": 100},
            {"name": "延长路", "lines": ["1号线"], "district": "静安区", "opening_year": 1996, "x": 180, "y": 100},
            {"name": "上海马戏城", "lines": ["1号线"], "district": "静安区", "opening_year": 1996, "x": 190, "y": 100},
            {"name": "汶水路", "lines": ["1号线"], "district": "静安区", "opening_year": 2004, "x": 200, "y": 100},
            {"name": "彭浦新村", "lines": ["1号线"], "district": "静安区", "opening_year": 2004, "x": 210, "y": 100},
            {"name": "共康路", "lines": ["1号线"], "district": "宝山区", "opening_year": 2004, "x": 220, "y": 100},
            {"name": "通河新村", "lines": ["1号线"], "district": "宝山区", "opening_year": 2004, "x": 230, "y": 100},
            {"name": "呼兰路", "lines": ["1号线"], "district": "宝山区", "opening_year": 2004, "x": 240, "y": 100},
            {"name": "共富新村", "lines": ["1号线"], "district": "宝山区", "opening_year": 2004, "x": 250, "y": 100},
            {"name": "宝安公路", "lines": ["1号线"], "district": "宝山区", "opening_year": 2004, "x": 260, "y": 100},
            {"name": "友谊西路", "lines": ["1号线"], "district": "宝山区", "opening_year": 2007, "x": 270, "y": 100},
            {"name": "富锦路", "lines": ["1号线"], "district": "宝山区", "opening_year": 2007, "x": 280, "y": 100},
            
            # 2号线
            {"name": "徐泾东", "lines": ["2号线"], "district": "青浦区", "opening_year": 2010, "x": 0, "y": 150},
            {"name": "虹桥火车站", "lines": ["2号线", "10号线", "17号线"], "district": "闵行区", "opening_year": 2010, "x": 10, "y": 150},
            {"name": "虹桥2号航站楼", "lines": ["2号线", "10号线"], "district": "闵行区", "opening_year": 2010, "x": 20, "y": 150},
            {"name": "淞虹路", "lines": ["2号线"], "district": "长宁区", "opening_year": 2006, "x": 30, "y": 150},
            {"name": "北新泾", "lines": ["2号线"], "district": "长宁区", "opening_year": 2006, "x": 40, "y": 150},
            {"name": "威宁路", "lines": ["2号线"], "district": "长宁区", "opening_year": 2006, "x": 50, "y": 150},
            {"name": "娄山关路", "lines": ["2号线", "15号线"], "district": "长宁区", "opening_year": 2006, "x": 60, "y": 150},
            {"name": "中山公园", "lines": ["2号线", "3号线", "4号线"], "district": "长宁区", "opening_year": 1999, "x": 70, "y": 150},
            {"name": "江苏路", "lines": ["2号线", "11号线"], "district": "长宁区", "opening_year": 1999, "x": 80, "y": 150},
            {"name": "静安寺", "lines": ["2号线", "7号线", "14号线"], "district": "静安区", "opening_year": 1999, "x": 90, "y": 150},
            {"name": "南京西路", "lines": ["2号线", "12号线", "13号线"], "district": "静安区", "opening_year": 1999, "x": 100, "y": 150},
            {"name": "人民广场", "lines": ["1号线", "2号线", "8号线"], "district": "黄浦区", "opening_year": 1999, "x": 130, "y": 150},
            {"name": "南京东路", "lines": ["2号线", "10号线"], "district": "黄浦区", "opening_year": 1999, "x": 140, "y": 150},
            {"name": "陆家嘴", "lines": ["2号线"], "district": "浦东新区", "opening_year": 1999, "x": 150, "y": 150},
            {"name": "东昌路", "lines": ["2号线"], "district": "浦东新区", "opening_year": 1999, "x": 160, "y": 150},
            {"name": "世纪大道", "lines": ["2号线", "4号线", "6号线", "9号线"], "district": "浦东新区", "opening_year": 1999, "x": 170, "y": 150},
            {"name": "上海科技馆", "lines": ["2号线"], "district": "浦东新区", "opening_year": 2000, "x": 180, "y": 150},
            {"name": "世纪公园", "lines": ["2号线"], "district": "浦东新区", "opening_year": 2000, "x": 190, "y": 150},
            {"name": "龙阳路", "lines": ["2号线", "7号线", "16号线", "18号线", "磁浮"], "district": "浦东新区", "opening_year": 2000, "x": 200, "y": 150},
            {"name": "张江高科", "lines": ["2号线"], "district": "浦东新区", "opening_year": 2000, "x": 210, "y": 150},
            {"name": "金科路", "lines": ["2号线"], "district": "浦东新区", "opening_year": 2010, "x": 220, "y": 150},
            {"name": "广兰路", "lines": ["2号线"], "district": "浦东新区", "opening_year": 2010, "x": 230, "y": 150},
            {"name": "唐镇", "lines": ["2号线"], "district": "浦东新区", "opening_year": 2010, "x": 240, "y": 150},
            {"name": "创新中路", "lines": ["2号线"], "district": "浦东新区", "opening_year": 2010, "x": 250, "y": 150},
            {"name": "华夏东路", "lines": ["2号线"], "district": "浦东新区", "opening_year": 2010, "x": 260, "y": 150},
            {"name": "川沙", "lines": ["2号线"], "district": "浦东新区", "opening_year": 2010, "x": 270, "y": 150},
            {"name": "凌空路", "lines": ["2号线"], "district": "浦东新区", "opening_year": 2010, "x": 280, "y": 150},
            {"name": "远东大道", "lines": ["2号线"], "district": "浦东新区", "opening_year": 2010, "x": 290, "y": 150},
            {"name": "海天三路", "lines": ["2号线"], "district": "浦东新区", "opening_year": 2010, "x": 300, "y": 150},
            {"name": "浦东国际机场", "lines": ["2号线", "磁浮"], "district": "浦东新区", "opening_year": 2010, "x": 310, "y": 150},
            
            # 3号线
            {"name": "上海南站", "lines": ["1号线", "3号线", "15号线"], "district": "徐汇区", "opening_year": 2000, "x": 50, "y": 50},
            {"name": "石龙路", "lines": ["3号线"], "district": "徐汇区", "opening_year": 2000, "x": 60, "y": 50},
            {"name": "龙漕路", "lines": ["3号线", "12号线"], "district": "徐汇区", "opening_year": 2000, "x": 70, "y": 50},
            {"name": "漕溪路", "lines": ["3号线"], "district": "徐汇区", "opening_year": 2000, "x": 80, "y": 50},
            {"name": "宜山路", "lines": ["3号线", "4号线", "9号线"], "district": "徐汇区", "opening_year": 2000, "x": 90, "y": 50},
            {"name": "虹桥路", "lines": ["3号线", "4号线", "10号线"], "district": "长宁区", "opening_year": 2000, "x": 100, "y": 50},
            {"name": "延安西路", "lines": ["3号线", "4号线"], "district": "长宁区", "opening_year": 2000, "x": 110, "y": 50},
            {"name": "中山公园", "lines": ["2号线", "3号线", "4号线"], "district": "长宁区", "opening_year": 2000, "x": 70, "y": 150},
            {"name": "金沙江路", "lines": ["3号线", "4号线", "13号线"], "district": "普陀区", "opening_year": 2000, "x": 80, "y": 200},
            {"name": "曹杨路", "lines": ["3号线", "4号线", "11号线"], "district": "普陀区", "opening_year": 2000, "x": 90, "y": 200},
            {"name": "镇坪路", "lines": ["3号线", "4号线", "7号线"], "district": "普陀区", "opening_year": 2000, "x": 100, "y": 200},
            {"name": "中潭路", "lines": ["3号线", "4号线"], "district": "普陀区", "opening_year": 2000, "x": 110, "y": 200},
            {"name": "上海火车站", "lines": ["1号线", "3号线", "4号线"], "district": "静安区", "opening_year": 2000, "x": 160, "y": 200},
            {"name": "宝山路", "lines": ["3号线", "4号线"], "district": "静安区", "opening_year": 2000, "x": 170, "y": 200},
            {"name": "东宝兴路", "lines": ["3号线"], "district": "虹口区", "opening_year": 2000, "x": 180, "y": 200},
            {"name": "虹口足球场", "lines": ["3号线", "8号线"], "district": "虹口区", "opening_year": 2000, "x": 190, "y": 200},
            {"name": "赤峰路", "lines": ["3号线"], "district": "虹口区", "opening_year": 2000, "x": 200, "y": 200},
            {"name": "大柏树", "lines": ["3号线"], "district": "虹口区", "opening_year": 2000, "x": 210, "y": 200},
            {"name": "江湾镇", "lines": ["3号线"], "district": "虹口区", "opening_year": 2000, "x": 220, "y": 200},
            {"name": "殷高西路", "lines": ["3号线"], "district": "宝山区", "opening_year": 2006, "x": 230, "y": 200},
            {"name": "长江南路", "lines": ["3号线"], "district": "宝山区", "opening_year": 2006, "x": 240, "y": 200},
            {"name": "淞发路", "lines": ["3号线"], "district": "宝山区", "opening_year": 2006, "x": 250, "y": 200},
            {"name": "张华浜", "lines": ["3号线"], "district": "宝山区", "opening_year": 2006, "x": 260, "y": 200},
            {"name": "淞滨路", "lines": ["3号线"], "district": "宝山区", "opening_year": 2006, "x": 270, "y": 200},
            {"name": "水产路", "lines": ["3号线"], "district": "宝山区", "opening_year": 2006, "x": 280, "y": 200},
            {"name": "宝杨路", "lines": ["3号线"], "district": "宝山区", "opening_year": 2006, "x": 290, "y": 200},
            {"name": "友谊路", "lines": ["3号线"], "district": "宝山区", "opening_year": 2006, "x": 300, "y": 200},
            {"name": "铁力路", "lines": ["3号线"], "district": "宝山区", "opening_year": 2006, "x": 310, "y": 200},
            {"name": "江杨北路", "lines": ["3号线"], "district": "宝山区", "opening_year": 2006, "x": 320, "y": 200},
            
            # 4号线（环线部分站点）
            {"name": "宜山路", "lines": ["3号线", "4号线", "9号线"], "district": "徐汇区", "opening_year": 2005, "x": 90, "y": 50},
            {"name": "上海体育馆", "lines": ["1号线", "4号线"], "district": "徐汇区", "opening_year": 2005, "x": 70, "y": 100},
            {"name": "上海体育场", "lines": ["4号线"], "district": "徐汇区", "opening_year": 2005, "x": 75, "y": 110},
            {"name": "东安路", "lines": ["4号线", "7号线"], "district": "徐汇区", "opening_year": 2005, "x": 85, "y": 110},
            {"name": "大木桥路", "lines": ["4号线", "12号线"], "district": "徐汇区", "opening_year": 2005, "x": 95, "y": 110},
            {"name": "鲁班路", "lines": ["4号线"], "district": "黄浦区", "opening_year": 2005, "x": 105, "y": 110},
            {"name": "西藏南路", "lines": ["4号线", "8号线"], "district": "黄浦区", "opening_year": 2005, "x": 115, "y": 110},
            {"name": "南浦大桥", "lines": ["4号线"], "district": "黄浦区", "opening_year": 2005, "x": 125, "y": 110},
            {"name": "塘桥", "lines": ["4号线"], "district": "浦东新区", "opening_year": 2005, "x": 135, "y": 110},
            {"name": "蓝村路", "lines": ["4号线", "6号线"], "district": "浦东新区", "opening_year": 2005, "x": 145, "y": 110},
            {"name": "世纪大道", "lines": ["2号线", "4号线", "6号线", "9号线"], "district": "浦东新区", "opening_year": 2005, "x": 170, "y": 150},
            {"name": "浦东大道", "lines": ["4号线", "14号线"], "district": "浦东新区", "opening_year": 2005, "x": 180, "y": 140},
            {"name": "杨树浦路", "lines": ["4号线"], "district": "杨浦区", "opening_year": 2005, "x": 190, "y": 130},
            {"name": "大连路", "lines": ["4号线", "12号线"], "district": "杨浦区", "opening_year": 2005, "x": 200, "y": 120},
            {"name": "临平路", "lines": ["4号线"], "district": "虹口区", "opening_year": 2005, "x": 210, "y": 110},
            {"name": "海伦路", "lines": ["4号线", "10号线"], "district": "虹口区", "opening_year": 2005, "x": 220, "y": 100},
            {"name": "宝山路", "lines": ["3号线", "4号线"], "district": "静安区", "opening_year": 2005, "x": 230, "y": 90},
            {"name": "上海火车站", "lines": ["1号线", "3号线", "4号线"], "district": "静安区", "opening_year": 2005, "x": 160, "y": 200},
            
            # 8号线
            {"name": "市光路", "lines": ["8号线"], "district": "杨浦区", "opening_year": 2007, "x": 250, "y": 80},
            {"name": "嫩江路", "lines": ["8号线"], "district": "杨浦区", "opening_year": 2007, "x": 240, "y": 85},
            {"name": "翔殷路", "lines": ["8号线"], "district": "杨浦区", "opening_year": 2007, "x": 230, "y": 90},
            {"name": "黄兴公园", "lines": ["8号线"], "district": "杨浦区", "opening_year": 2007, "x": 220, "y": 95},
            {"name": "延吉中路", "lines": ["8号线"], "district": "杨浦区", "opening_year": 2007, "x": 210, "y": 100},
            {"name": "黄兴路", "lines": ["8号线"], "district": "杨浦区", "opening_year": 2007, "x": 200, "y": 105},
            {"name": "江浦路", "lines": ["8号线", "18号线"], "district": "杨浦区", "opening_year": 2007, "x": 190, "y": 110},
            {"name": "鞍山新村", "lines": ["8号线"], "district": "杨浦区", "opening_year": 2007, "x": 180, "y": 115},
            {"name": "四平路", "lines": ["8号线", "10号线"], "district": "杨浦区", "opening_year": 2007, "x": 170, "y": 120},
            {"name": "曲阳路", "lines": ["8号线"], "district": "虹口区", "opening_year": 2007, "x": 160, "y": 125},
            {"name": "虹口足球场", "lines": ["3号线", "8号线"], "district": "虹口区", "opening_year": 2007, "x": 150, "y": 130},
            {"name": "西藏北路", "lines": ["8号线"], "district": "静安区", "opening_year": 2007, "x": 140, "y": 135},
            {"name": "中兴路", "lines": ["8号线"], "district": "静安区", "opening_year": 2007, "x": 130, "y": 140},
            {"name": "曲阜路", "lines": ["8号线", "12号线"], "district": "静安区", "opening_year": 2007, "x": 120, "y": 145},
            {"name": "人民广场", "lines": ["1号线", "2号线", "8号线"], "district": "黄浦区", "opening_year": 2007, "x": 130, "y": 150},
            {"name": "大世界", "lines": ["8号线", "14号线"], "district": "黄浦区", "opening_year": 2007, "x": 140, "y": 155},
            {"name": "老西门", "lines": ["8号线", "10号线"], "district": "黄浦区", "opening_year": 2007, "x": 150, "y": 160},
            {"name": "陆家浜路", "lines": ["8号线", "9号线"], "district": "黄浦区", "opening_year": 2007, "x": 160, "y": 165},
            {"name": "西藏南路", "lines": ["4号线", "8号线"], "district": "黄浦区", "opening_year": 2007, "x": 170, "y": 170},
            {"name": "中华艺术宫", "lines": ["8号线"], "district": "浦东新区", "opening_year": 2012, "x": 180, "y": 175},
            {"name": "耀华路", "lines": ["7号线", "8号线"], "district": "浦东新区", "opening_year": 2007, "x": 190, "y": 180},
            {"name": "成山路", "lines": ["8号线", "13号线"], "district": "浦东新区", "opening_year": 2007, "x": 200, "y": 185},
            {"name": "杨思", "lines": ["8号线"], "district": "浦东新区", "opening_year": 2007, "x": 210, "y": 190},
            {"name": "东方体育中心", "lines": ["6号线", "8号线", "11号线"], "district": "浦东新区", "opening_year": 2011, "x": 220, "y": 195},
            {"name": "凌兆新村", "lines": ["8号线"], "district": "浦东新区", "opening_year": 2009, "x": 230, "y": 200},
            {"name": "芦恒路", "lines": ["8号线"], "district": "浦东新区", "opening_year": 2009, "x": 240, "y": 205},
            {"name": "浦江镇", "lines": ["8号线"], "district": "闵行区", "opening_year": 2009, "x": 250, "y": 210},
            {"name": "江月路", "lines": ["8号线"], "district": "闵行区", "opening_year": 2009, "x": 260, "y": 215},
            {"name": "联航路", "lines": ["8号线"], "district": "闵行区", "opening_year": 2009, "x": 270, "y": 220},
            {"name": "沈杜公路", "lines": ["8号线"], "district": "闵行区", "opening_year": 2009, "x": 280, "y": 225},
        ]
        
        # 处理站点数据
        for station in station_data:
            name = station["name"]
            lines = station["lines"]  # 已经是"X号线"格式
            
            # 存储站点信息
            self.stations[name] = {
                "district": station["district"],
                "lines": lines,
                "opening_year": station["opening_year"],
                "position": {"x": station["x"], "y": station["y"]}
            }
            
            # 存储站点线路关系
            for line in lines:
                self.station_lines[name].add(line)
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
                    "position": {"x": station["x"], "y": station["y"]}
                }
    
    def build_graph(self):
        """构建地铁网络图"""
        # 构建每条线路上的连接
        for line, stations in self.lines.items():
            for i in range(len(stations) - 1):
                station_a = stations[i]
                station_b = stations[i + 1]
                
                # 创建节点ID
                node_a = f"{station_a}_{line}"
                node_b = f"{station_b}_{line}"
                
                # 添加双向连接（权重为1，表示一站）
                self.graph[node_a].append((node_b, 1))
                self.graph[node_b].append((node_a, 1))
        
        # 添加换乘站内部的连接（同站不同线之间的换乘通道）
        station_groups = defaultdict(list)
        
        for node_id, info in self.station_nodes.items():
            station_name = info["station_name"]
            station_groups[station_name].append(node_id)
        
        # 对于每个换乘站，连接所有线路节点（换乘通道，权重为0.5表示换乘时间）
        for station_name, nodes in station_groups.items():
            if len(nodes) > 1:  # 换乘站
                for i in range(len(nodes)):
                    for j in range(i + 1, len(nodes)):
                        self.graph[nodes[i]].append((nodes[j], 0.5))  # 换乘时间
                        self.graph[nodes[j]].append((nodes[i], 0.5))
    
    def find_shortest_path(self, start_station: str, end_station: str) -> Tuple[int, int, List[str]]:
        """
        使用Dijkstra算法计算最短路径
        
        返回: (最小站数, 最小换乘次数, 路径节点列表)
        """
        if start_station == end_station:
            return 0, 0, []
        
        # 获取起点和终点的所有节点（不同线路）
        start_nodes = [node for node in self.station_nodes if node.startswith(start_station + "_")]
        end_nodes = [node for node in self.station_nodes if node.startswith(end_station + "_")]
        
        if not start_nodes or not end_nodes:
            return float('inf'), float('inf'), []
        
        # Dijkstra算法
        dist = {}
        prev = {}
        visited = set()
        pq = []
        
        # 初始化
        for node in start_nodes:
            dist[node] = 0
            heapq.heappush(pq, (0, node))
        
        # Dijkstra主循环
        while pq:
            current_dist, current_node = heapq.heappop(pq)
            
            if current_node in visited:
                continue
            visited.add(current_node)
            
            # 如果到达任一终点节点
            current_station = current_node.split("_")[0]
            if current_station == end_station:
                # 重建路径
                path = []
                node = current_node
                while node is not None:
                    path.append(node)
                    node = prev.get(node)
                path.reverse()
                
                # 计算站数和换乘次数
                stations_visited = set()
                transfers = 0
                current_line = None
                
                for node in path:
                    station_name = node.split("_")[0]
                    line_name = node.split("_")[1]
                    stations_visited.add(station_name)
                    
                    if current_line is not None and current_line != line_name:
                        transfers += 1
                    current_line = line_name
                
                # 站数是访问的唯一站点数减1（起点不计入）
                station_count = len(stations_visited) - 1
                
                return station_count, transfers, path
            
            # 遍历邻居
            for neighbor, weight in self.graph[current_node]:
                if neighbor in visited:
                    continue
                
                new_dist = current_dist + weight
                if neighbor not in dist or new_dist < dist[neighbor]:
                    dist[neighbor] = new_dist
                    prev[neighbor] = current_node
                    heapq.heappush(pq, (new_dist, neighbor))
        
        # 没有找到路径
        return float('inf'), float('inf'), []
    
    def calculate_min_stations(self, start_station: str, end_station: str) -> int:
        """计算最小站数"""
        stations, _, _ = self.find_shortest_path(start_station, end_station)
        return stations if stations != float('inf') else 100  # 默认值
    
    def calculate_min_transfers(self, start_station: str, end_station: str) -> int:
        """计算最小换乘次数"""
        _, transfers, _ = self.find_shortest_path(start_station, end_station)
        return transfers if transfers != float('inf') else 10  # 默认值
    
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
        answer = random.choice(all_stations)
        
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
    info = metro_graph.get_station_info(station_name)
    if info:
        return jsonify({'success': True, 'info': info})
    return jsonify({'success': False, 'error': '站点不存在'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)