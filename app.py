import streamlit as st
import numpy as np

# --- ロジック部分 ---
def calculate_expressiveness_score(intonation_raw, technique_raw):
    """抑揚と技法点の実数値から表現力スコアを算出する。"""
    intonation_axis = [0.0, 45.0, 70.0, 80.0, 90.0, 100.0]
    technique_axis = [0.0, 40.0, 60.0, 80.0, 90.0, 100.0]
    score_grid = [
        [0, 30000, 40000, 50000, 53000, 55000],
        [30000, 50000, 65000, 78000, 82000, 83500],
        [50000, 63000, 75000, 86000, 88500, 92000],
        [56000, 66000, 80000, 89000, 92500, 95000],
        [60000, 68000, 82000, 93100, 95000, 97500],
        [63000, 70000, 84000, 95000, 98000, 100000]
    ]
    
    def find_axis_index(value, axis):
        if value >= 100.0: return len(axis) - 2
        for i in range(len(axis) - 1):
            if axis[i] <= value < axis[i+1]: return i
        return len(axis) - 2

    idx_i = find_axis_index(intonation_raw, intonation_axis)
    idx_t = find_axis_index(technique_raw, technique_axis)
    intonation_ratio = (intonation_raw - intonation_axis[idx_i]) / (intonation_axis[idx_i+1] - intonation_axis[idx_i])
    technique_ratio = (technique_raw - technique_axis[idx_t]) / (technique_axis[idx_t+1] - technique_axis[idx_t])
    q11, q12, q21, q22 = score_grid[idx_i][idx_t], score_grid[idx_i][idx_t+1], score_grid[idx_i+1][idx_t], score_grid[idx_i+1][idx_t+1]
    return (1-intonation_ratio)*(1-technique_ratio)*q11 + intonation_ratio*(1-technique_ratio)*q21 + (1-intonation_ratio)*technique_ratio*q12 + intonation_ratio*technique_ratio*q22

def interpolate_jh_bonus(jh_count, accent_count):
    """
    画像のJHボーナス表に基づき、2次元線形補間を行う。
    ※表の値は10倍してボーナス実数値として扱う。
    """
    jh_axis = [0.0, 10.0, 20.0, 30.0, 40.0, 50.0]
    acc_axis = [0.0, 10.0, 20.0, 30.0, 40.0, 50.0]
    # 表の値を10倍した実測値テーブル
    bonus_table = [
        [0,  0,  0, 0, 0, 0], 
        [100, 50,  0, 0, 0, 0], 
        [200, 100, 50, 30, 20, 10], 
        [300, 200, 80, 40, 30, 20], 
        [400, 250, 90, 50, 30, 20], 
        [500, 300, 100, 50, 30, 20]
    ]

    acc_val = max(0.0, min(50.0, float(accent_count)))
    
    # JH数が50を超える場合の外挿
    if jh_count > 50.0:
        b40 = interpolate_jh_bonus(40.0, acc_val)
        b50 = interpolate_jh_bonus(50.0, acc_val)
        slope = (b50 - b40)
        return b50 + slope * ((jh_count - 50.0) / 10.0)

    jh_val = max(0.0, float(jh_count))
    def get_idx(val, axis):
        for i in range(len(axis)-1):
            if axis[i] <= val <= axis[i+1]: return i
        return len(axis)-2

    i, j = get_idx(jh_val, jh_axis), get_idx(acc_val, acc_axis)
    r_jh = (jh_val - jh_axis[i]) / (jh_axis[i+1] - jh_axis[i])
    r_acc = (acc_val - acc_axis[j]) / (acc_axis[j+1] - acc_axis[j])
    b11, b12, b21, b22 = bonus_table[i][j], bonus_table[i][j+1], bonus_table[i+1][j], bonus_table[i+1][j+1]
    
    return (1-r_jh)*(1-r_acc)*b11 + r_jh*(1-r_acc)*b21 + (1-r_jh)*r_acc*b12 + r_jh*r_acc*b22

def solve_possible_bonus_range(display_intonation, display_expressiveness, base_technique_points):
    """境界条件に基づき、合計技法点の範囲からボーナス範囲を類推する。"""
    intonation_min = display_intonation * 10
    intonation_max = min(display_intonation * 10 + 9, 1000)
    expressiveness_min = display_expressiveness * 1000
    expressiveness_max = min(display_expressiveness * 1000 + 999, 100000)
    
    min_total_t = None
    for t in range(0, 1251):
        if calculate_expressiveness_score(intonation_max / 10.0, t / 12.5) >= expressiveness_min:
            min_total_t = t
            break
    max_total_t = None
    for t in range(1250, -1, -1):
        if calculate_expressiveness_score(intonation_min / 10.0, t / 12.5) <= expressiveness_max:
            max_total_t = t
            break

    if min_total_t is None or max_total_t is None or min_total_t > max_total_t:
        return []

    possible_bonuses = []
    for t in range(min_total_t, max_total_t + 1):
        bonus = t - base_technique_points
        if bonus >= 0:
            possible_bonuses.append(bonus)
    return sorted(list(set(possible_bonuses)))

# --- Streamlit UI ---
st.set_page_config(page_title="JH Bonus Analyzer", page_icon="🎯")
st.title("💥 ジャストヒットボーナス解析")

analysis_mode = st.radio("解析精度を選択", ("【予測】みかけの数値から推定する", "【正確】実数値から特定する"), horizontal=True)
st.divider()

if analysis_mode == "【予測】みかけの数値から推定する":
    st.subheader("🔍 みかけ数値推定モード")
    col_i, col_s = st.columns(2)
    with col_i: input_disp_i = st.number_input("みかけの抑揚 (0-100)", 0, 100, 100)
    with col_s: input_disp_s = st.number_input("みかけの表現力 (0-100)", 0, 100, 100)
    
    col_base, col_acc = st.columns(2)
    with col_base: input_base_t = st.number_input("基礎技法点 (0-1250)", 0, 1250, 1050)
    with col_acc: input_acc = st.number_input("アクセント数 (0以上の整数)", min_value=0, value=0, step=1)

    if st.button("範囲を類推する", type="primary", use_container_width=True):
        bonus_results = solve_possible_bonus_range(input_disp_i, input_disp_s, input_base_t)
        if bonus_results:
            b_min, b_max = min(bonus_results), max(bonus_results)
            st.success("解析完了")
            
            if b_min == b_max: st.metric("確定ボーナス値", f"{b_min} 点")
            else: st.subheader(f"ボーナス推定範囲: {b_min} ～ {b_max} 点")
            
            st.info(f"💡 アクセント数 {input_acc} の時のJH数類推")
            jh_results = []
            # 探索範囲を 0.0 ～ 200.0 程度に拡大
            for test_jh in np.arange(0.0, 200.1, 0.1):
                calc_b = interpolate_jh_bonus(test_jh, input_acc)
                if any(abs(calc_b - b) < 0.5 for b in bonus_results):
                    jh_results.append(round(test_jh, 1))
            
            if jh_results:
                jh_min, jh_max = min(jh_results), max(jh_results)
                if jh_min == jh_max: st.write(f"該当するJH数: **{jh_min}**")
                else: st.write(f"該当するJH数範囲: **{jh_min} ～ {jh_max}**")
            else:
                st.write("該当するJH数は見つかりませんでした。")
        else:
            st.error("条件に合うボーナスが見つかりませんでした。")

else:
    # 詳細解析モードも同様に修正（中略）
    st.subheader("📋 詳細リザルト解析モード")
    col_ri, col_rs = st.columns(2)
    with col_ri: input_real_i = st.number_input("実際の抑揚 (0-1000)", 0, 1000, 1000)
    with col_rs: input_real_s = st.number_input("実際の表現力 (0-100000)", 0, 100000, 100000)
    
    col_rb, col_ra = st.columns(2)
    with col_rb: input_base_t_precise = st.number_input("基礎技法点 (0-1250)", 0, 1250, 1050)
    with col_ra: input_acc_precise = st.number_input("アクセント数 (0以上の整数)", min_value=0, value=0, step=1)

    if st.button("ボーナスを特定", type="primary", use_container_width=True):
        best_t, min_diff = 0, float('inf')
        for t in range(0, 1251):
            diff = abs(calculate_expressiveness_score(input_real_i / 10.0, t / 12.5) - input_real_s)
            if diff < min_diff: min_diff, best_t = diff, t
        
        bonus = best_t - input_base_t_precise
        if bonus < 0: st.error("基礎点が合計値を上回っています。")
        else:
            st.success("解析完了")
            st.metric("ジャストヒットボーナス", f"{bonus} 点")
            jh_candidates = []
            for test_jh in np.arange(0.0, 200.1, 0.1):
                if abs(interpolate_jh_bonus(test_jh, input_acc_precise) - bonus) < 0.5:
                    jh_candidates.append(round(test_jh, 1))
            if jh_candidates:
                st.write(f"推定されるJH数: **{min(jh_candidates)} ～ {max(jh_candidates)}**")

st.divider()
st.caption("© 2026 Zawasow_lab")