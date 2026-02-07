import csv
import os
from datetime import datetime, timedelta, date
from lunar_python import Solar
from chinese_calendar import is_holiday, is_workday, get_holiday_detail

# 获取 chinese-calendar 支持的年份范围（硬编码，因其未提供 API）
# 根据官方文档和源码，通常为 2004 至 2030 年（截至 2025 年）
CHINESE_CALENDAR_MIN_YEAR = 2004
CHINESE_CALENDAR_MAX_YEAR = 2030

# 预定义常量映射表（避免在循环中重复创建）
WEEKDAY_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def validate_date_range(start: date, end: date):
    """验证日期是否在 chinese-calendar 支持的范围内"""
    if start.year < CHINESE_CALENDAR_MIN_YEAR or end.year > CHINESE_CALENDAR_MAX_YEAR:
        raise ValueError(
            f"日期范围超出 chinese-calendar 支持的年份 [{CHINESE_CALENDAR_MIN_YEAR}, {CHINESE_CALENDAR_MAX_YEAR}]。\n"
            f"您输入的范围：{start} 至 {end}"
        )


def generate_calendar_csv(start_date_str, end_date_str, output_file="calendar_output.csv"):
    """
    生成指定公历日期范围内的日历数据（含农历、节气、法定节假日），并保存为 CSV。
    
    :param start_date_str: 起始日期字符串，格式 'YYYY-MM-DD'
    :param end_date_str: 结束日期字符串，格式 'YYYY-MM-DD'
    :param output_file: 输出的 CSV 文件名
    """
    # 解析输入日期
    try:
        start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        end = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError("日期格式错误，请使用 YYYY-MM-DD 格式。") from e

    if start > end:
        raise ValueError("起始日期不能晚于结束日期")

    # 检查是否在 chinese-calendar 支持范围内
    validate_date_range(start, end)

    # 准备 CSV 头部
    fieldnames = [
        "公历日期",  # 添加原始公历日期字段
        "公历年", "公历月", "公历日", "公历旬", "周数", "星期",
        "农历年", "农历月", "农历日", "是否闰月", "农历节日",
        "生肖",
        "节气",
        "是否节假日", "是否工作日", "节日名称"
    ]

    # 确保输出文件夹存在
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, mode='w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        current = start
        while current <= end:
            # 公历信息
            g_year = current.year
            g_month = current.month
            g_day = current.day
            weekday = WEEKDAY_NAMES[current.weekday()]
            # 上中下旬判断（修复索引越界问题）
            if 1 <= g_day <= 10:
                shang_zhong_xia = "上旬"
            elif 11 <= g_day <= 20:
                shang_zhong_xia = "中旬"
            else:
                shang_zhong_xia = "下旬"
            # 周数计算（ISO周数）
            week_number = current.isocalendar()[1]

            # 农历转换
            solar = Solar.fromYmd(g_year, g_month, g_day)
            lunar = solar.getLunar()

            l_year = lunar.getYear()
            l_month = lunar.getMonth()
            l_day = lunar.getDay()
            is_leap = l_month < 0  # 负数月份表示闰月
            
            # 获取农历节日信息（优化：简化合并过程）
            festivals = lunar.getFestivals() or []
            other_festivals = lunar.getOtherFestivals() or []
            
            # 合并节日信息并格式化
            all_festivals = festivals + other_festivals
            lunar_festival = ", ".join(all_festivals) if all_festivals else ""
            
            # 特别处理一些重要的传统节日（如果需要）
            # 例如：检查是否为元宵节、小年等重要节日
            # 这里使用lunar-python库自动识别的节日信息
            
            shengxiao = lunar.getYearShengXiao()

            # 节气（如“立春”、“清明”等，若无则返回空字符串）
            jieqi = lunar.getJieQi() or ""

            # 节假日判断（优化：减少不必要的函数调用和简化逻辑）
            is_hol = is_holiday(current)
            # 工作日判断（优化：根据is_hol推导，减少一次函数调用）
            is_work = not is_hol if is_hol else is_workday(current)
            
            # 获取节日名称
            hol_name = ""
            if is_hol:
                _, name = get_holiday_detail(current)
                hol_name = name or ""

            # 写入一行
            row = {
                "公历日期": current.strftime("%Y-%m-%d"),  # 添加原始公历日期字段
                "公历年": g_year,
                "公历月": g_month,
                "公历日": g_day,
                "公历旬": shang_zhong_xia,
                "周数": week_number,
                "星期": weekday,
                "农历年": l_year,
                "农历月": abs(l_month),  # 将负数月份转换为正数
                "农历日": l_day,
                "是否闰月": "是" if is_leap else "否",
                "农历节日": lunar_festival,
                "生肖": shengxiao,
                "节气": jieqi,
                "是否节假日": "是" if is_hol else "否",
                "是否工作日": "是" if is_work else "否",
                "节日名称": hol_name
            }
            writer.writerow(row)

            current += timedelta(days=1)

    print(f"✅ 日历数据已成功导出至：{output_file}")


if __name__ == "__main__":
    try:
        # 交互式输入起止日期
        print("====================================")
        print("       日历数据生成工具")
        print("====================================")
        
        # 获取开始日期
        current_year = date.today().year
        start_date = input(f"请输入开始日期（格式：YYYY-MM-DD，默认：{current_year}-01-01）: ").strip()
        if not start_date:
            start_date = f"{current_year}-01-01"
        
        # 获取结束日期
        end_date = input(f"请输入结束日期（格式：YYYY-MM-DD，默认：{current_year}-12-31）: ").strip()
        if not end_date:
            end_date = f"{current_year}-12-31"
        
        print("\n正在生成日历数据...")
        
        # 根据开始日期和结束日期自动生成输出文件名
        start_date_str = start_date.replace("-", "")
        end_date_str = end_date.replace("-", "")
        output_file = f"output/{start_date_str}-{end_date_str}_chinese_calendar.csv"
        
        generate_calendar_csv(start_date, end_date, output_file)
        
    except ValueError as e:
        print(f"❌ 输入错误：{e}")
    except Exception as e:
        print(f"❌ 程序运行出错：{e}")