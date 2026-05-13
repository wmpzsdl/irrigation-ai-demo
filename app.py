"""
================================
土壤灌溉 AI 决策系统 Demo
================================

运行方式：streamlit run app.py

环境要求：
- Python 3.8+
- streamlit >= 1.28.0
- pandas >= 1.3.0
- numpy >= 1.20.0
- plotly >= 5.0.0
- pillow >= 8.0.0

文件要求：
- app.py 与 "明集镇卫星定位图.png" 需要在同一目录
- 或在第一次运行时自动生成测试用的卫星定位图

功能说明：
1. 首页：显示6块农田的卫星地图，可点击进入田块详情
2. 详情页：展示土壤监测数据、气象预报、灌溉决策建议、财务分析

作者: AI 农业决策系统
日期: 2024
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from PIL import Image, ImageDraw
import os
import json

# ============================================================================
# 页面配置
# ============================================================================
st.set_page_config(
    page_title="AI 灌溉决策系统",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 自定义CSS样式
st.markdown("""
<style>
    :root {
        --primary-color: #2ecc71;
        --secondary-color: #3498db;
        --warning-color: #f39c12;
        --danger-color: #e74c3c;
        --dark-bg: #1a1a1a;
        --light-bg: #f8f9fa;
    }

    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }

    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        min-height: 100vh;
    }

    .stTitle {
        color: #2c3e50;
        font-weight: 700;
        font-size: 2.8em;
        margin-bottom: 0.5em;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }

    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-left: 4px solid #2ecc71;
        transition: all 0.3s ease;
    }

    .metric-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
    }

    .chart-container {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin: 1rem 0;
    }

    .button-primary {
        background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
        color: white;
        padding: 0.8rem 2rem;
        border-radius: 8px;
        border: none;
        cursor: pointer;
        font-weight: 600;
        transition: all 0.3s;
    }

    .button-primary:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 16px rgba(46, 204, 113, 0.3);
    }

    .comparison-table {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        margin: 1rem 0;
    }

    .field-marker {
        font-weight: 600;
        padding: 0.4rem 0.8rem;
        border-radius: 6px;
        display: inline-block;
        margin: 0.3rem;
        cursor: pointer;
        transition: all 0.3s;
    }

    .field-marker:hover {
        transform: scale(1.1);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# 数据定义
# ============================================================================

FIELDS_DATA = {
    "明集北场田": {
        "location": "明集镇北，张庄村东",
        "longitude": 117.81,
        "latitude": 37.20,
        "area": 42,
        "crop": "冬小麦",
        "color": "#e74c3c",
        "map_x": 980,  # 像素坐标（相对于卫星图）
        "map_y": 200,
    },
    "明集南洼田": {
        "location": "明集镇南，小李庄西",
        "longitude": 117.80,
        "latitude": 37.17,
        "area": 38,
        "crop": "冬小麦",
        "color": "#3498db",
        "map_x": 980,
        "map_y": 1200,
    },
    "明集东河滩田": {
        "location": "明集镇东，徒骇河附近",
        "longitude": 117.83,
        "latitude": 37.19,
        "area": 55,
        "crop": "夏玉米",
        "color": "#2ecc71",
        "map_x": 1400,
        "map_y": 1000,
    },
    "明集西岗田": {
        "location": "明集镇西，西闸村北",
        "longitude": 117.78,
        "latitude": 37.18,
        "area": 48,
        "crop": "冬小麦",
        "color": "#f39c12",
        "map_x": 430,
        "map_y": 880,
    },
    "明集核心示范田": {
        "location": "明集镇政府南1km",
        "longitude": 117.81,
        "latitude": 37.18,
        "area": 65,
        "crop": "冬小麦+玉米轮作",
        "color": "#9b59b6",
        "map_x": 1040,
        "map_y": 820,
    },
    "明集东南试验田": {
        "location": "明集镇东南，杏行村",
        "longitude": 117.84,
        "latitude": 37.16,
        "area": 30,
        "crop": "夏玉米",
        "color": "#1abc9c",
        "map_x": 1360,
        "map_y": 1250,
    },
}


# ============================================================================
# 数据生成函数
# ============================================================================

def generate_satellite_image(width=1000, height=500):
    """
    生成模拟的卫星定位图
    如果使用真实卫星图，请替换此函数
    """
    img = Image.new("RGB", (width, height), color=(34, 139, 34))  # 深绿色背景
    draw = ImageDraw.Draw(img, 'RGBA')

    # 添加地形纹理
    np.random.seed(42)
    for i in range(width):
        for j in range(height):
            if np.random.random() > 0.95:
                x = i + np.random.randint(-5, 5)
                y = j + np.random.randint(-5, 5)
                if 0 <= x < width and 0 <= y < height:
                    draw.point((x, y), fill=(30, 130, 30))

    # 绘制河流
    for i in range(int(width * 0.6), width, 3):
        y = int(150 + 50 * np.sin(i * 0.01))
        draw.ellipse([i - 5, y - 5, i + 5, y + 5], fill=(70, 130, 180))

    # 绘制道路
    draw.rectangle([400, 250, 600, 260], fill=(200, 180, 100))

    return img


def create_satellite_with_markers(img):
    """
    在卫星图上添加田块标记
    """
    draw = ImageDraw.Draw(img, 'RGBA')

    for field_name, field_info in FIELDS_DATA.items():
        x = field_info["map_x"]
        y = field_info["map_y"]

        # 绘制圆形标记
        radius = 25
        color_hex = field_info["color"]
        rgb = tuple(int(color_hex[i:i + 2], 16) for i in (1,3,5))

        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=(*rgb, 200),
            outline=(255, 255, 255, 255),
            width=3
        )

        # 绘制田块名称标签
        font_size = 12
        label = field_name[:4]  # 显示缩写
        draw.text(
            (x + 30, y - 10),
            label,
            fill=(0, 0, 0, 255)
        )

    return img


def generate_soil_data(field_name, days=7):
    """
    生成模拟的土壤传感器数据（最近7天）
    """
    np.random.seed(hash(field_name) % 2 ** 32)

    # 不同田块有不同的基准湿度
    base_moisture = {
        "明集北场田": 55,
        "明集南洼田": 48,
        "明集东河滩田": 72,
        "明集西岗田": 52,
        "明集核心示范田": 60,
        "明集东南试验田": 68,
    }

    moisture_base = base_moisture.get(field_name, 60)

    dates = [datetime.now() - timedelta(days=i) for i in range(days, 0, -1)]

    # 生成湿度数据（呈下降趋势）
    moisture = []
    current = moisture_base
    for i in range(days):
        current = current - np.random.uniform(1, 3) + np.random.uniform(-1, 1)
        moisture.append(np.clip(current, 20, 85))

    # 生成温度数据
    temperature = [15 + 8 * np.sin(i * np.pi / days) + np.random.uniform(-2, 2) for i in range(days)]

    # 生成电导率数据
    ec = [0.8 + 0.3 * np.sin(i * np.pi / days) + np.random.uniform(-0.1, 0.1) for i in range(days)]

    df = pd.DataFrame({
        "日期": dates,
        "土壤湿度(%)": moisture,
        "土壤温度(℃)": temperature,
        "电导率EC(mS/cm)": ec,
    })

    return df


def generate_weather_forecast():
    """
    生成模拟的气象预报（未来3天）
    """
    days = ["明天", "后天", "第3天"]
    high_temp = [24, 22, 26]
    low_temp = [15, 12, 14]
    rainfall_prob = [30, 60, 20]

    return pd.DataFrame({
        "日期": days,
        "最高气温(℃)": high_temp,
        "最低气温(℃)": low_temp,
        "降雨概率(%)": rainfall_prob,
    })


def calculate_irrigation_decision(field_name, current_moisture, trend, rainfall_prob):
    """
    根据土壤湿度、趋势、降雨概率生成灌溉决策
    """

    LOWER_THRESHOLD = 45
    UPPER_THRESHOLD = 75

    decision = {
        "需要灌溉": False,
        "灌溉量(mm)": 0,
        "最佳灌溉时间": "无需灌溉",
        "决策理由": "",
        "优先级": "正常",
    }

    # 考虑降雨因素
    effective_moisture = current_moisture + rainfall_prob * 0.15

    if effective_moisture < LOWER_THRESHOLD:
        decision["需要灌溉"] = True
        decision["灌溉量(mm)"] = min(40, int((UPPER_THRESHOLD - effective_moisture) * 0.5))
        decision["最佳灌溉时间"] = "立即灌溉"
        decision["优先级"] = "紧急"
        decision["决策理由"] = f"土壤湿度低于阈值({LOWER_THRESHOLD}%)，且降雨概率低。建议立即灌溉。"
    elif effective_moisture < LOWER_THRESHOLD + 5:
        decision["需要灌溉"] = True
        decision["灌溉量(mm)"] = 20
        decision["最佳灌溉时间"] = "今天下午或明天上午"
        decision["优先级"] = "高"
        decision["决策理由"] = f"土壤湿度接近下限，趋势向下（{trend:.2f}%/天）。建议及时灌溉。"
    elif rainfall_prob > 50 and current_moisture > LOWER_THRESHOLD - 10:
        decision["需要灌溉"] = False
        decision["最佳灌溉时间"] = "等待降雨"
        decision["优先级"] = "低"
        decision["决策理由"] = f"降雨概率高（{rainfall_prob}%），建议暂缓灌溉，观察天气变化。"
    else:
        decision["需要灌溉"] = False
        decision["最佳灌溉时间"] = "暂无需灌溉"
        decision["优先级"] = "正常"
        decision["决策理由"] = "土壤湿度处于适宜范围，暂无灌溉需求。"

    return decision


# ============================================================================
# Session State 管理
# ============================================================================

if "page" not in st.session_state:
    st.session_state.page = "map"
    st.session_state.selected_field = None


# ============================================================================
# 首页：地图展示
# ============================================================================

def show_map_page():
    """显示农田地图主页"""

    col_title = st.columns([1, 0.2])[0]
    with col_title:
        st.markdown("# 🚜 明集镇农田监测地图")
        st.markdown("### 山东省滨州市滨城区明集镇 - AI 灌溉决策系统")

    st.markdown("---")

    # 检查或生成卫星图
    satellite_image_path = "明集镇卫星定位图.png"

    if not os.path.exists(satellite_image_path):
        # 生成测试用的卫星图
        with st.info("⚠️ 未检测到卫星定位图，已自动生成测试图像。请将实际的卫星图放在 app.py 同一目录。"):
            satellite_img = generate_satellite_image()
            satellite_img.save(satellite_image_path)
    else:
        satellite_img = Image.open(satellite_image_path)

    # 添加田块标记
    satellite_img_marked = satellite_img.copy()
    satellite_img_marked = create_satellite_with_markers(satellite_img_marked)

    # 显示地图
    st.markdown("### 卫星定位图")
    col_map = st.columns(1)[0]
    with col_map:
        st.image(satellite_img_marked, use_column_width=True)

    st.markdown("---")

    # 田块信息卡片
    st.markdown("### 📍 选择田块查看详情")

    cols = st.columns(3)
    for idx, (field_name, field_info) in enumerate(FIELDS_DATA.items()):
        with cols[idx % 3]:
            st.markdown(f"""
            <div class="metric-card">
                <h4 style="color: {field_info['color']}; margin-bottom: 0.5rem;">
                    {field_name}
                </h4>
                <p style="font-size: 0.9rem; color: #666;">
                    📍 {field_info['location']}<br/>
                    🌾 {field_info['crop']}<br/>
                    📐 {field_info['area']} 亩
                </p>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"查看详情: {field_name}", key=f"btn_{idx}"):
                st.session_state.page = "detail"
                st.session_state.selected_field = field_name
                st.rerun()

    st.markdown("---")

    # 统计信息
    st.markdown("### 📊 农场总体统计")

    col1, col2, col3, col4 = st.columns(4)

    total_area = sum(f["area"] for f in FIELDS_DATA.values())
    with col1:
        st.metric("总田块数", len(FIELDS_DATA), "块")

    with col2:
        st.metric("总耕种面积", total_area, "亩")

    with col3:
        wheat_fields = sum(1 for f in FIELDS_DATA.values() if "小麦" in f["crop"])
        st.metric("冬小麦田块", wheat_fields, "块")

    with col4:
        corn_fields = sum(1 for f in FIELDS_DATA.values() if "玉米" in f["crop"])
        st.metric("夏玉米田块", corn_fields, "块")

    st.markdown("---")
    st.markdown("""
    **使用说明：**
    - 点击上方卡片中的"查看详情"按钮，进入具体田块的监测和决策界面
    - 实时显示土壤水热盐的动态变化，基于大数据算法生成灌溉方案
    - 可视化展示AI灌溉决策相比传统灌溉的经济效益
    """)


# ============================================================================
# 详情页：田块监测与决策
# ============================================================================

def show_detail_page():
    """显示田块详情和灌溉决策"""

    field_name = st.session_state.selected_field
    if field_name not in FIELDS_DATA:
        st.error("田块不存在")
        return

    field_info = FIELDS_DATA[field_name]

    # 返回按钮
    col_header = st.columns([0.15, 0.85])
    with col_header[0]:
        if st.button("⬅️ 返回地图", key="btn_back"):
            st.session_state.page = "map"
            st.session_state.selected_field = None
            st.rerun()

    with col_header[1]:
        st.markdown(f"# {field_name}")
        st.markdown(
            f"**位置：** {field_info['location']} | **作物：** {field_info['crop']} | **面积：** {field_info['area']} 亩")

    st.markdown("---")

    # 获取数据
    soil_df = generate_soil_data(field_name, days=7)
    weather_df = generate_weather_forecast()
    current_moisture = soil_df["土壤湿度(%)"].iloc[-1]
    moisture_trend = (soil_df["土壤湿度(%)"].iloc[-1] - soil_df["土壤湿度(%)"].iloc[-3]) / 2

    # 左右两栏布局
    col_left, col_right = st.columns([0.6, 0.4])

    # ========== 左侧：数据和决策 ==========
    with col_left:
        st.markdown("### 📈 土壤监测数据（最近7天）")

        # 创建交互式图表
        fig = go.Figure()

        # 土壤湿度
        fig.add_trace(go.Scatter(
            x=soil_df["日期"],
            y=soil_df["土壤湿度(%)"],
            name="土壤湿度(%)",
            mode="lines+markers",
            line=dict(color="#3498db", width=3),
            marker=dict(size=8),
            yaxis="y1"
        ))

        # 土壤温度
        fig.add_trace(go.Scatter(
            x=soil_df["日期"],
            y=soil_df["土壤温度(℃)"],
            name="土壤温度(℃)",
            mode="lines+markers",
            line=dict(color="#e74c3c", width=3),
            marker=dict(size=8),
            yaxis="y2"
        ))

        # 电导率
        fig.add_trace(go.Scatter(
            x=soil_df["日期"],
            y=soil_df["电导率EC(mS/cm)"],
            name="电导率EC",
            mode="lines+markers",
            line=dict(color="#2ecc71", width=3),
            marker=dict(size=8),
            yaxis="y3"
        ))

        # 添加阈值线
        fig.add_hline(y=45, line_dash="dash", line_color="red", annotation_text="下限(45%)")
        fig.add_hline(y=75, line_dash="dash", line_color="orange", annotation_text="上限(75%)")

        fig.update_layout(
            title="土壤水热盐综合监测",
            hovermode="x unified",
            height=450,
            xaxis=dict(title="日期", domain=[0, 0.85]),
            yaxis=dict(title="土壤湿度(%)", color="#3498db"),
            yaxis2=dict(title="土壤温度(℃)", color="#e74c3c", overlaying="y", side="right"),
            yaxis3=dict(title="电导率(mS/cm)", color="#2ecc71", overlaying="y", side="right", anchor="x", position=0.85,
                        showticklabels=False),
            plot_bgcolor="rgba(240,240,240,0.5)",
            margin=dict(r=120)
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        st.markdown("### 📊 关键指标")

        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

        with metric_col1:
            st.markdown(f"""
            <div class="metric-card">
                <p style="color: #888; font-size: 0.9rem; margin-bottom: 0.5rem;">当前湿度</p>
                <h3 style="color: #3498db; margin: 0;">{current_moisture:.1f}%</h3>
            </div>
            """, unsafe_allow_html=True)

        with metric_col2:
            avg_moisture = soil_df["土壤湿度(%)"].mean()
            st.markdown(f"""
            <div class="metric-card">
                <p style="color: #888; font-size: 0.9rem; margin-bottom: 0.5rem;">历史平均</p>
                <h3 style="color: #9b59b6; margin: 0;">{avg_moisture:.1f}%</h3>
            </div>
            """, unsafe_allow_html=True)

        with metric_col3:
            st.markdown(f"""
            <div class="metric-card">
                <p style="color: #888; font-size: 0.9rem; margin-bottom: 0.5rem;">下限阈值</p>
                <h3 style="color: #e74c3c; margin: 0;">45%</h3>
            </div>
            """, unsafe_allow_html=True)

        with metric_col4:
            st.markdown(f"""
            <div class="metric-card">
                <p style="color: #888; font-size: 0.9rem; margin-bottom: 0.5rem;">上限阈值</p>
                <h3 style="color: #f39c12; margin: 0;">75%</h3>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("### 🌤️ 气象预报（未来3天）")

        weather_display = weather_df.copy()
        weather_display.columns = ["日期", "最高温(℃)", "最低温(℃)", "降雨概率(%)"]
        st.dataframe(weather_display, use_container_width=True, hide_index=True)

        st.markdown("---")

        st.markdown("### 🤖 AI灌溉决策")

        if st.button("生成灌溉方案", key="btn_decision"):
            st.session_state.show_decision = True

        if st.session_state.get("show_decision", False):
            rainfall_prob = weather_df["降雨概率(%)"].iloc[0]
            decision = calculate_irrigation_decision(field_name, current_moisture, moisture_trend, rainfall_prob)

            # 显示决策结果
            decision_status = "✅ 无需灌溉" if not decision["需要灌溉"] else "⚠️ 需要灌溉"

            st.markdown(f"""
            <div class="metric-card" style="border-left-color: {'#e74c3c' if decision['需要灌溉'] else '#2ecc71'};">
                <h4 style="color: {'#e74c3c' if decision['需要灌溉'] else '#2ecc71'}; margin-bottom: 1rem;">
                    {decision_status}
                </h4>

                <p style="font-size: 1rem; margin: 0.5rem 0;">
                    <strong>灌溉量：</strong> {decision['灌溉量(mm)']} mm
                </p>
                <p style="font-size: 1rem; margin: 0.5rem 0;">
                    <strong>最佳灌溉时间：</strong> {decision['最佳灌溉时间']}
                </p>
                <p style="font-size: 1rem; margin: 0.5rem 0;">
                    <strong>优先级：</strong> {decision['优先级']}
                </p>
                <hr style="margin: 1rem 0;">
                <p style="font-size: 0.95rem; color: #555; line-height: 1.6;">
                    <strong>决策理由：</strong><br/>
                    {decision['决策理由']}
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("### 💰 经济效益分析")

        # 财务数据
        traditional_water = 450  # mm/season
        ai_water = 315  # mm/season (30% 节水)
        water_saving_rate = 30
        yield_increase_rate = 15

        tab1, tab2 = st.tabs(["效率对比", "成本分析"])

        with tab1:
            comparison_df = pd.DataFrame({
                "指标": ["用水量(mm/季)", "增产率(%)", "节水率(%)", "年均亩收益(元)"],
                "传统灌溉": [traditional_water, 0, 0, 4200],
                "AI智能灌溉": [ai_water, yield_increase_rate, water_saving_rate, 5250],
                "增益": [
                    f"-{traditional_water - ai_water}mm",
                    f"+{yield_increase_rate}%",
                    f"+{water_saving_rate}%",
                    f"+¥{5250 - 4200}"
                ]
            })

            st.dataframe(comparison_df, use_container_width=True, hide_index=True)

        with tab2:
            cost_df = pd.DataFrame({
                "成本项目": [
                    "灌溉成本(元/亩·季)",
                    "人工成本(元/亩·季)",
                    "肥料成本(元/亩·季)",
                    "总成本(元/亩·季)"
                ],
                "传统灌溉": [180, 150, 320, 650],
                "AI智能灌溉": [126, 100, 280, 506],
            })

            st.dataframe(cost_df, use_container_width=True, hide_index=True)

            st.markdown("""
            **主要优势：**
            - 💧 节水30%：通过精准灌溉降低用水成本
            - 🌾 增产15%：优化灌溉时间和用量，提高产量
            - 💰 成本降低22%：综合降低灌溉和人工成本
            - 📈 年亩增收¥1,050：显著提升经济效益
            """)

    # ========== 右侧：实时监控 ==========
    with col_right:
        st.markdown("### 📹 实时监控")

        st.info("""
        **农田实时监控视频**

        可嵌入B站视频：
        https://www.bilibili.com/video/BV11hrPYYEAJ/

        或替换为：
        - 本地农田实时录像
        - 无人机监控画面
        - IP摄像头直播
        """)

        # 显示一个占位图
        placeholder_img = Image.new("RGB", (400, 300), color=(200, 200, 200))
        draw = ImageDraw.Draw(placeholder_img)
        draw.text((100, 130), "Real-time Monitoring", fill=(100, 100, 100))
        st.image(placeholder_img, caption="实时监控画面（点击上方链接观看）")

        st.markdown("---")

        st.markdown("### 📋 田块基本信息")

        st.markdown(f"""
        | 信息项 | 详情 |
        |------|------|
        | 田块名称 | {field_name} |
        | 位置 | {field_info['location']} |
        | 坐标 | {field_info['longitude']}, {field_info['latitude']} |
        | 面积 | {field_info['area']} 亩 |
        | 作物 | {field_info['crop']} |
        | 监测时间 | {soil_df['日期'].iloc[-1].strftime('%Y-%m-%d %H:%M')} |
        """)

        st.markdown("---")

        st.markdown("### ⚙️ 快速操作")

        if st.button("📱 发送灌溉通知", use_container_width=True):
            st.success("✅ 灌溉通知已发送至农户手机")

        if st.button("🔄 刷新数据", use_container_width=True):
            st.rerun()

        if st.button("💾 导出报告", use_container_width=True):
            st.success("✅ 报告已生成")


# ============================================================================
# 主程序
# ============================================================================

def main():
    if st.session_state.page == "map":
        show_map_page()
    elif st.session_state.page == "detail":
        show_detail_page()


if __name__ == "__main__":
    main()
