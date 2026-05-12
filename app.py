import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import random

# ============================================================================
# 1. 页面配置
# ============================================================================
st.set_page_config(
    page_title="土壤灌溉决策系统",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义 CSS（清爽农业主题）
st.markdown("""
    <style>
    * {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }

    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 0;
    }

    .stMetric {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 12px;
        padding: 16px;
        border-left: 4px solid #2ecc71;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }

    .header-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a5f3d;
        margin-bottom: 8px;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .header-subtitle {
        font-size: 1.1rem;
        color: #555;
        margin-bottom: 20px;
    }

    .field-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        margin: 8px 0;
        border-left: 5px solid #27ae60;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        cursor: pointer;
        transition: all 0.3s ease;
    }

    .field-card:hover {
        transform: translateX(4px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    .decision-box-yes {
        background-color: #d5f4e6;
        border-left: 5px solid #27ae60;
        padding: 16px;
        border-radius: 8px;
        margin: 12px 0;
    }

    .decision-box-no {
        background-color: #fef5e7;
        border-left: 5px solid #f39c12;
        padding: 16px;
        border-radius: 8px;
        margin: 12px 0;
    }

    .reason-text {
        color: #2c3e50;
        font-size: 0.95rem;
        line-height: 1.5;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================================================
# 2. 农田数据定义
# ============================================================================
FIELDS_DATA = {
    "field_001": {
        "name": "明集北场田",
        "location": "明集镇北，张庄村东300米",
        "lat": 37.2045,
        "lon": 117.8125,
        "area": 42,
        "crop": "冬小麦",
        "soil_type": "壤土"
    },
    "field_002": {
        "name": "明集南洼田",
        "location": "明集镇南，小李庄西",
        "lat": 37.1725,
        "lon": 117.8015,
        "area": 38,
        "crop": "冬小麦",
        "soil_type": "粘壤土"
    },
    "field_003": {
        "name": "明集东河滩田",
        "location": "明集镇东，徒骇河附近",
        "lat": 37.1895,
        "lon": 117.8335,
        "area": 55,
        "crop": "夏玉米",
        "soil_type": "沙壤土"
    },
    "field_004": {
        "name": "明集西岗田",
        "location": "明集镇西，西闸村北",
        "lat": 37.1815,
        "lon": 117.7805,
        "area": 48,
        "crop": "冬小麦",
        "soil_type": "壤土"
    },
    "field_005": {
        "name": "明集核心示范田",
        "location": "明集镇政府南1km",
        "lat": 37.1785,
        "lon": 117.8125,
        "area": 65,
        "crop": "冬小麦+玉米轮作",
        "soil_type": "壤土"
    },
    "field_006": {
        "name": "明集东南试验田",
        "location": "明集镇东南，杏行村",
        "lat": 37.1605,
        "lon": 117.8415,
        "area": 30,
        "crop": "夏玉米",
        "soil_type": "沙壤土"
    }
}


# ============================================================================
# 3. Mock 土壤数据生成
# ============================================================================
def generate_soil_data(field_id):
    """为指定田块生成最近 7 天的土壤数据"""
    np.random.seed(hash(field_id) % 2 ** 32)  # 确保同一田块数据一致

    dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]

    # 根据土壤类型调整基础值
    field_info = FIELDS_DATA[field_id]
    soil_type = field_info["soil_type"]

    if soil_type == "沙壤土":
        humidity_base = 50
        temp_base = 18
    elif soil_type == "粘壤土":
        humidity_base = 65
        temp_base = 16
    else:  # 壤土
        humidity_base = 58
        temp_base = 17

    # 模拟缓慢下降的湿度趋势 + 随机波动
    humidity = [humidity_base - i * 2 + np.random.normal(0, 2) for i in range(7)]
    humidity = [max(30, min(80, h)) for h in humidity]  # 限制在 30-80

    # 温度变化（日间波动）
    temperature = [temp_base + np.random.normal(0, 1.5) for _ in range(7)]
    temperature = [max(5, min(35, t)) for t in temperature]

    # EC（电导率）相对稳定，轻微波动
    ec = [0.8 + np.random.normal(0, 0.15) for _ in range(7)]
    ec = [max(0.3, min(2.0, e)) for e in ec]

    return pd.DataFrame({
        "date": dates,
        "humidity": humidity,
        "temperature": temperature,
        "ec": ec
    })


# ============================================================================
# 4. 初始化 Session State
# ============================================================================
if "current_page" not in st.session_state:
    st.session_state.current_page = "map"  # "map" 或 "detail"
if "selected_field" not in st.session_state:
    st.session_state.selected_field = None


# ============================================================================
# 5. 灌溉决策引擎（规则模拟）
# ============================================================================
def generate_irrigation_decision(field_id, soil_data):
    """基于土壤数据生成灌溉方案"""
    current_humidity = soil_data["humidity"].iloc[-1]
    avg_humidity = soil_data["humidity"].mean()
    humidity_trend = soil_data["humidity"].iloc[-1] - soil_data["humidity"].iloc[-3]

    # 模拟未来降雨（这里用随机值）
    rain_probability = np.random.randint(0, 80)

    field_info = FIELDS_DATA[field_id]
    crop = field_info["crop"]

    # 灌溉阈值（根据作物调整）
    if "小麦" in crop:
        lower_threshold = 45
        upper_threshold = 75
    else:  # 玉米
        lower_threshold = 40
        upper_threshold = 70

    # 决策逻辑
    need_irrigation = False
    irrigation_amount = 0
    best_time = ""
    reason = ""

    if current_humidity < lower_threshold:
        if rain_probability < 30:  # 未来降雨概率低
            need_irrigation = True
            deficit = lower_threshold - current_humidity
            irrigation_amount = max(20, min(40, deficit * 0.8))
            best_time = "今天傍晚（18-20 点）"
            reason = f"土壤湿度{current_humidity:.1f}%已低于下限{lower_threshold}%，预报降雨概率{rain_probability}%较低，需及时灌溉补水。"
        else:
            need_irrigation = False
            best_time = "-"
            reason = f"虽然湿度较低（{current_humidity:.1f}%），但未来3天降雨概率{rain_probability}%较高，建议观察后再决定。"

    elif current_humidity > upper_threshold:
        need_irrigation = False
        best_time = "-"
        reason = f"土壤湿度{current_humidity:.1f}%已处于良好状态，暂不需灌溉。建议继续监测。"

    else:
        # 在中间范围，根据趋势判断
        if humidity_trend < -5 and rain_probability < 40:
            need_irrigation = True
            irrigation_amount = 15
            best_time = "明早（6-8 点）"
            reason = f"湿度处于中等偏干（{current_humidity:.1f}%），近期下降趋势明显，预报降雨概率{rain_probability}%较低。建议轻灌。"
        else:
            need_irrigation = False
            best_time = "-"
            reason = f"土壤湿度{current_humidity:.1f}%处于适宜范围，可继续观察。"

    return {
        "need_irrigation": need_irrigation,
        "irrigation_amount": irrigation_amount,
        "best_time": best_time,
        "reason": reason,
        "rain_probability": rain_probability,
        "current_humidity": current_humidity,
        "avg_humidity": avg_humidity
    }


# ============================================================================
# 6. 地图绘制函数
# ============================================================================
def create_field_map():
    """创建农田地图"""
    # 中心点：明集镇中心
    center_lat = 37.185
    center_lon = 117.810

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=14,
        tiles="OpenStreetMap"
    )

    # 添加所有田块标记
    for field_id, field_info in FIELDS_DATA.items():
        popup_text = f"""
        <b>{field_info['name']}</b><br>
        位置: {field_info['location']}<br>
        面积: {field_info['area']} 亩<br>
        作物: {field_info['crop']}
        """

        folium.Marker(
            location=[field_info['lat'], field_info['lon']],
            popup=folium.Popup(popup_text, max_width=250),
            tooltip=field_info['name'],
            icon=folium.Icon(color='green', icon='leaf', prefix='fa')
        ).add_to(m)

    return m


# ============================================================================
# 7. 绘制土壤数据曲线
# ============================================================================
def create_soil_chart(soil_data):
    """创建土壤三参数曲线图"""
    fig = make_subplots(
        rows=1, cols=1,
        specs=[[{"secondary_y": True}]]
    )

    # 湿度（左 Y 轴）
    fig.add_trace(
        go.Scatter(
            x=soil_data['date'],
            y=soil_data['humidity'],
            name='土壤湿度 (%)',
            line=dict(color='#3498db', width=3),
            fill='tozeroy',
            fillcolor='rgba(52, 152, 219, 0.2)',
            mode='lines+markers',
            marker=dict(size=8)
        ),
        secondary_y=False
    )

    # 温度（左 Y 轴）
    fig.add_trace(
        go.Scatter(
            x=soil_data['date'],
            y=soil_data['temperature'],
            name='土壤温度 (℃)',
            line=dict(color='#e74c3c', width=3),
            mode='lines+markers',
            marker=dict(size=8)
        ),
        secondary_y=False
    )

    # EC（右 Y 轴）
    fig.add_trace(
        go.Scatter(
            x=soil_data['date'],
            y=soil_data['ec'],
            name='电导率 (µS/cm)',
            line=dict(color='#f39c12', width=3),
            mode='lines+markers',
            marker=dict(size=8),
            yaxis='y2'
        ),
        secondary_y=True
    )

    # 设置 Y 轴标签
    fig.update_yaxes(title_text="<b>湿度 (%) / 温度 (℃)</b>", secondary_y=False, range=[0, 100])
    fig.update_yaxes(title_text="<b>电导率 (µS/cm)</b>", secondary_y=True, range=[0, 2.5])

    # 设置 X 轴
    fig.update_xaxes(title_text="<b>日期</b>")

    # 整体美化
    fig.update_layout(
        title="<b>最近 7 天土壤参数趋势</b>",
        hovermode='x unified',
        template='plotly_white',
        height=450,
        font=dict(size=11),
        legend=dict(orientation='v', x=0.02, y=0.98)
    )

    return fig


# ============================================================================
# 8. 页面逻辑：地图界面
# ============================================================================
def page_map():
    st.markdown("<div class='header-title'>🌾 土壤灌溉 AI 决策系统</div>", unsafe_allow_html=True)
    st.markdown("<div class='header-subtitle'>滨州市滨城区明集镇 · 实时灌溉方案生成</div>", unsafe_allow_html=True)

    st.write("---")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("📍 田块分布地图")
        field_map = create_field_map()
        map_data = st_folium(field_map, width=1200, height=500)

        # 地图点击后处理
        if map_data and map_data['last_clicked']:
            clicked_lat = map_data['last_clicked']['lat']
            clicked_lon = map_data['last_clicked']['lng']

            # 查找最近的田块
            for field_id, field_info in FIELDS_DATA.items():
                dist = abs(field_info['lat'] - clicked_lat) + abs(field_info['lon'] - clicked_lon)
                if dist < 0.01:  # 足够接近
                    st.session_state.selected_field = field_id
                    st.session_state.current_page = "detail"
                    st.rerun()

    with col2:
        st.subheader("📋 田块列表")
        for field_id, field_info in FIELDS_DATA.items():
            with st.container():
                st.markdown(f"""
                <div class='field-card' onclick="document.querySelector('[data-field-id={field_id}]').click()">
                    <b>{field_info['name']}</b><br>
                    <small>{field_info['crop']}</small><br>
                    <small>面积: {field_info['area']} 亩</small>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"查看详情", key=f"btn_{field_id}"):
                    st.session_state.selected_field = field_id
                    st.session_state.current_page = "detail"
                    st.rerun()


# ============================================================================
# 9. 页面逻辑：田块详情界面
# ============================================================================
def page_detail():
    field_id = st.session_state.selected_field
    field_info = FIELDS_DATA[field_id]

    # 返回地图按钮
    if st.button("← 返回地图"):
        st.session_state.current_page = "map"
        st.session_state.selected_field = None
        st.rerun()

    st.markdown(f"<div class='header-title'>🌾 {field_info['name']}</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='header-subtitle'>
        📍 {field_info['location']} · 
        🌾 {field_info['crop']} · 
        📐 {field_info['area']} 亩
    </div>
    """, unsafe_allow_html=True)

    st.write("---")

    # 生成数据
    soil_data = generate_soil_data(field_id)

    # 第一行：关键指标卡片
    st.subheader("📊 关键指标")
    metric_cols = st.columns(4)

    current_humidity = soil_data["humidity"].iloc[-1]
    avg_humidity = soil_data["humidity"].mean()
    current_temp = soil_data["temperature"].iloc[-1]
    current_ec = soil_data["ec"].iloc[-1]

    with metric_cols[0]:
        st.metric("当前土壤湿度", f"{current_humidity:.1f}%",
                  delta=f"{current_humidity - soil_data['humidity'].iloc[-2]:.1f}%")

    with metric_cols[1]:
        st.metric("7日平均湿度", f"{avg_humidity:.1f}%")

    with metric_cols[2]:
        st.metric("当前土壤温度", f"{current_temp:.1f}℃")

    with metric_cols[3]:
        st.metric("电导率", f"{current_ec:.2f} µS/cm")

    st.write("")

    # 第二行：土壤数据曲线
    st.subheader("📈 7日数据趋势")
    fig_soil = create_soil_chart(soil_data)
    st.plotly_chart(fig_soil, use_container_width=True)

    # 第三行：阈值信息
    st.subheader("⚙️ 灌溉阈值")
    threshold_cols = st.columns(2)

    if "小麦" in field_info["crop"]:
        lower_threshold = 45
        upper_threshold = 75
    else:
        lower_threshold = 40
        upper_threshold = 70

    with threshold_cols[0]:
        st.info(f"**湿度下限阈值**: {lower_threshold}% (作物生长所需最低值)")

    with threshold_cols[1]:
        st.warning(f"**湿度上限阈值**: {upper_threshold}% (防止根部腐烂)")

    st.write("")

    # 第四行：气象预报（模拟）
    st.subheader("🌤️ 未来 3 日气象预报（模拟）")
    forecast_data = {
        "日期": ["今天", "明天", "后天"],
        "最高温 (℃)": [28 + np.random.randint(-2, 3), 26 + np.random.randint(-2, 3), 25 + np.random.randint(-2, 3)],
        "最低温 (℃)": [18 + np.random.randint(-1, 2), 16 + np.random.randint(-1, 2), 15 + np.random.randint(-1, 2)],
        "降雨概率 (%)": [10 + np.random.randint(0, 20), 20 + np.random.randint(0, 30), 15 + np.random.randint(0, 25)]
    }
    forecast_df = pd.DataFrame(forecast_data)
    st.dataframe(forecast_df, use_container_width=True, hide_index=True)

    st.write("")

    # 第五行：灌溉决策
    st.subheader("💡 灌溉决策方案")

    if st.button("🚀 生成灌溉方案", type="primary", use_container_width=True):
        decision = generate_irrigation_decision(field_id, soil_data)
        st.session_state.decision = decision

    # 显示决策结果
    if "decision" in st.session_state:
        decision = st.session_state.decision

        st.write("")

        if decision["need_irrigation"]:
            st.markdown(f"""
            <div class='decision-box-yes'>
                <h3>✅ 建议灌溉</h3>
                <p class='reason-text'><b>灌溉量:</b> {decision['irrigation_amount']:.0f} mm</p>
                <p class='reason-text'><b>最佳灌溉时间:</b> {decision['best_time']}</p>
                <p class='reason-text'><b>决策理由:</b> {decision['reason']}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class='decision-box-no'>
                <h3>⏸️ 暂不灌溉</h3>
                <p class='reason-text'><b>当前土壤湿度:</b> {decision['current_humidity']:.1f}%</p>
                <p class='reason-text'><b>决策理由:</b> {decision['reason']}</p>
            </div>
            """, unsafe_allow_html=True)

        # 详细数据
        with st.expander("📋 详细决策数据"):
            detail_cols = st.columns(3)
            with detail_cols[0]:
                st.metric("当前湿度", f"{decision['current_humidity']:.1f}%")
            with detail_cols[1]:
                st.metric("7日平均湿度", f"{decision['avg_humidity']:.1f}%")
            with detail_cols[2]:
                st.metric("预报降雨概率", f"{decision['rain_probability']}%")


# ============================================================================
# 10. 主程序入口
# ============================================================================
def main():
    if st.session_state.current_page == "map":
        page_map()
    elif st.session_state.current_page == "detail":
        page_detail()


if __name__ == "__main__":
    main()
