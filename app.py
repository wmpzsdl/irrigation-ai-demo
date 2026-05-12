import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib

# 解决matplotlib后端冲突问题（必须加）
matplotlib.use('Agg')
# 解决中文显示乱码问题（Windows）
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ============ 页面配置 ============
st.set_page_config(
    page_title="AI灌溉决策系统",
    layout="wide",  # 宽屏模式，展示更多内容
    initial_sidebar_state="expanded"  # 默认展开侧边栏
)
st.title("🌾 AI灌溉决策系统 - 演示版")
st.markdown("---")

# ============ 侧边栏：选择农田 ============
st.sidebar.header("⚙️ 农田选择")

# 可根据你的项目修改农田信息（位置、面积、作物等）
farm_options = {
    "滨州明集镇（小麦）": {
        "location": "山东滨州市邹平市明集镇",
        "area": "50亩",
        "crop": "冬小麦",
        "last_irrigation": "2026-05-01",
        "soil_type": "壤土"
    },
    "寿光蔬菜园（蔬菜）": {
        "location": "山东潍坊市寿光市",
        "area": "100亩",
        "crop": "茄子、番茄",
        "last_irrigation": "2026-05-03",
        "soil_type": "菜园地"
    },
    "三河湖镇（水稻）": {
        "location": "山东滨州市三河湖镇",
        "area": "80亩",
        "crop": "水稻",
        "last_irrigation": "2026-05-05",
        "soil_type": "水稻田"
    }
}
selected_farm = st.sidebar.radio("选择农田：", list(farm_options.keys()))
farm_info = farm_options[selected_farm]
# 侧边栏展示选中农田的基本信息
st.sidebar.markdown(f"""
### 农田信息
- **位置：** {farm_info['location']}
- **面积：** {farm_info['area']}
- **作物：** {farm_info['crop']}
- **土壤类型：** {farm_info['soil_type']}
- **上次灌溉：** {farm_info['last_irrigation']}
""")

# ============ 主页面：土壤数据展示 ============
st.header(f"📊 {selected_farm} - 实时土壤监测")


# 生成模拟数据（实际项目中替换为从数据库/传感器读取）
def generate_soil_data(farm_name, days=7):
    """生成过去N天的土壤监测数据"""
    dates = [datetime.now() - timedelta(days=i) for i in range(days, 0, -1)]

    # 根据作物类型设置基础含水量和温度（可根据实际调整）
    if "小麦" in farm_name:
        base_humidity = 55
        base_temp = 18
    elif "蔬菜" in farm_name:
        base_humidity = 65
        base_temp = 25
    else:  # 水稻
        base_humidity = 75
        base_temp = 22

    data = {
        'date': [d.strftime("%m-%d") for d in dates],
        'humidity': [base_humidity + np.random.randn() * 5 - i * 0.5 for i in range(days)],  # 模拟含水量下降趋势
        'temperature': [base_temp + np.random.randn() * 2 for i in range(days)],
        'ec': [0.8 + np.random.randn() * 0.1 for i in range(days)],  # 土壤电导率
    }
    return pd.DataFrame(data)


# 生成数据并缓存（优化加载速度）
@st.cache_data
def get_cached_soil_data(farm_name):
    return generate_soil_data(farm_name)


soil_df = get_cached_soil_data(selected_farm)

# 显示4个关键指标卡片
col1, col2, col3, col4 = st.columns(4)

with col1:
    current_humidity = soil_df['humidity'].iloc[-1]
    st.metric(
        "土壤含水量",
        f"{current_humidity:.1f}%",
        f"{current_humidity - soil_df['humidity'].iloc[-2]:.1f}%",
        delta_color="inverse"  # 数值下降显示绿色，上升显示红色（符合灌溉逻辑）
    )

with col2:
    current_temp = soil_df['temperature'].iloc[-1]
    st.metric(
        "土壤温度",
        f"{current_temp:.1f}℃",
        f"{current_temp - soil_df['temperature'].iloc[-2]:.1f}℃"
    )

with col3:
    current_ec = soil_df['ec'].iloc[-1]
    st.metric(
        "电导率",
        f"{current_ec:.2f}",
        f"{current_ec - soil_df['ec'].iloc[-2]:.2f}"
    )

with col4:
    # 灌溉建议逻辑（可根据实际作物调整阈值）
    if current_humidity < 45:
        recommendation = "🔴 需要立即灌溉"
        color = "red"
    elif current_humidity < 55:
        recommendation = "🟡 建议近期灌溉"
        color = "orange"
    else:
        recommendation = "🟢 暂无需灌溉"
        color = "green"

    st.metric("灌溉建议", recommendation)

    # 绘制土壤含水量变化曲线
st.subheader("📈 土壤含水量变化曲线")
fig, ax = plt.subplots(figsize=(14, 5))  # 调整图表大小，更清晰
ax.plot(soil_df['date'], soil_df['humidity'], marker='o', linewidth=2, markersize=8, color='#2ecc71')
ax.axhline(y=45, color='r', linestyle='--', label='灌溉阈值（下界）', linewidth=2)
ax.axhline(y=65, color='b', linestyle='--', label='最优含水量（上界）', linewidth=2)
ax.fill_between(range(len(soil_df)), 45, 65, alpha=0.1, color='green')
ax.set_xlabel("日期", fontsize=12)
ax.set_ylabel("含水量（%）", fontsize=12)
ax.legend(loc='best', fontsize=10)
ax.grid(True, alpha=0.3)
st.pyplot(fig)

# 自动计算预计灌溉日期
humidity_drop_rate = (soil_df['humidity'].iloc[0] - soil_df['humidity'].iloc[-1]) / 7  # 日均下降量
days_to_threshold = (current_humidity - 45) / humidity_drop_rate
irrigation_date = datetime.now() + timedelta(days=days_to_threshold)
irrigation_date_str = irrigation_date.strftime("%Y年%m月%d日")

st.markdown(f"""
### 📌 数据解读
- **当前含水量：** {current_humidity:.1f}%
- **变化趋势：** 过去7天下降{soil_df['humidity'].iloc[0] - soil_df['humidity'].iloc[-1]:.1f}个百分点
- **预计何时需要灌溉：** 按当前下降速度，约在 **{irrigation_date_str}** 达到灌溉阈值
""")

# ============ AI决策模型 ============
st.header("🤖 AI灌溉决策模型")

st.markdown("""
我们采用 **LSTM + 随机森林集成模型** 预测作物需水量。

**模型架构：**
- 输入特征：土壤湿度、温度、电导率、气象数据（风速、降水）
- 模型：LSTM（处理时间序列） + 随机森林（特征融合）
- 输出：未来7天的推荐灌溉量

**在滨州的验证结果：**
- 灌溉精度：**85%+**
- 病虫害识别精度（YOLOv8）：**88%+**
""")

# 生成灌溉方案按钮
if st.button("🔥 生成灌溉方案", help="基于当前土壤数据生成AI建议"):
    st.success("✅ 正在调用模型...")

    # 模拟模型推理（实际项目中替换为调用真实训练好的模型）
    irrigation_scheme = {
        "time": "2026-05-09 上午8:00",
        "amount": 50,  # 毫米
        "frequency": "每5天灌溉一次",
        "water_saved": 30,  # 百分比
        "yield_increase": 15,  # 百分比
        "cost_saved": 40,  # 元/亩
        "confidence": 0.87  # 模型置信度
    }

    # 分两列显示灌溉建议和预期效益
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 灌溉建议")
        st.markdown(f"""
        - **何时灌溉：** {irrigation_scheme['time']}
        - **灌溉量：** {irrigation_scheme['amount']}mm
        - **灌溉频次：** {irrigation_scheme['frequency']}
        - **模型置信度：** {irrigation_scheme['confidence'] * 100:.0f}%
        """)

    with col2:
        st.subheader("💰 预期效益")
        st.markdown(f"""
        - **节水率：** ↓ {irrigation_scheme['water_saved']}%
        - **增产率：** ↑ {irrigation_scheme['yield_increase']}%
        - **成本节省：** ￥{irrigation_scheme['cost_saved']}/亩
        - **ROI：** {irrigation_scheme['cost_saved'] * 0.5}元（保守估计）
        """)

    # 传统灌溉vs AI灌溉对比
    st.markdown("### 📊 传统灌溉 vs AI灌溉")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.info(f"成本对比\n🔴 传统：150元\n🟢 AI：110元\n💚节省：**40元**")

    with col2:
        st.info(f"用水对比\n🔴 传统：500mm\n🟢 AI：350mm\n💚节省：**150mm**")

    with col3:
        st.info(f"增产对比\n🔴 传统：0%\n🟢 AI：+15%\n💚增加：**120斤/亩**")

    with col4:
        st.info(f"年均收益\n🔴 传统：0元\n🟢 AI：300+元\n💚收益：**5倍ROI**")

        # ============ 试点成果 ============
st.header("🎯 试点成果验证")

st.markdown("""
我们在山东三个地区的试点成果（实际农田，真实数据）：

| 地区 | 面积 | 病虫害防控 | 灌溉精度 | 节水率 | 增产率 |
|------|------|----------|--------|--------|--------|
| **寿光蔬菜园** | 5000亩 | ↓32% | 85%+ | 40% | 50% |
| **滨州明集镇** | 800亩 | ↓30% | 85%+ | 35% | 25% |
| **三河湖镇（水稻）** | 300亩 | ↓25% | 82% | 40% | 10% |
""")

# ============ 商业模式 ============
st.header("💼 商业模式与推广")

st.markdown("""
### 用户获取与盈利模式

**目标用户：** 山东小农户（2-50亩）和合作社

**收费模式：**
1. **SOP技术服务费**：100元/亩/年（或增产分成30%）
2. **溯源农产品溢价分成**：30-50%溢价，我们分成50%
3. **数据服务费**：为农业企业提供决策支持

**推广路径：**
1. 在县域建立示范园（试点验证）
2. 举办观摩会（农户看到实际效果）
3. 村级服务站代理（降低使用门槛）
4. "县域模板"复制到全国

**3年规划：**
- 2026年：10万亩，覆盖5个县
- 2027年：50万亩，覆盖20个县
- 2028年：100万亩+，成为全国标杆
""")

# ============ 页脚 ============
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; margin-top: 30px;'>
<p>🌾 数亩田 AI灌溉决策系统 | 驱动山东农业新质生产力</p>
<p>技术支持：山东大学人工智能学院 | 陈竹敏教授 / 林祺副教授</p>
</div>
""", unsafe_allow_html=True)