import json
import base64
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

def to_persian_num(number):
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    return "".join(persian_digits[int(d)] if d.isdigit() else d for d in str(number))

def _image_to_base64(image_path):
    """Convert an image file to base64 data URI for embedding in HTML."""
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        ext = Path(image_path).suffix.lower()
        mime_type = 'image/png' if ext == '.png' else 'image/jpeg'
        b64_data = base64.b64encode(image_data).decode('utf-8')
        return f"data:{mime_type};base64,{b64_data}"
    except Exception:
        return ""

def generate_dari_qa_report(survey, form_results, output_html_path, advanced_data=None):
    """Generates the official Dari HTML QA report based on Jinja2 template."""
    total_students = len(form_results)
    
    metadata = {
        "university": survey.university or "پوهنتون بدخشان",
        "faculty": survey.faculty or "پوهنحی کمپیوتر ساینس",
        "teacher_name": survey.professor or "نامعلوم",
        "subject": survey.subject or "نامعلوم",
        "department": survey.department or "نامعلوم",
        "semester": f"{survey.semester} / {survey.academic_year}",
        "total_students": to_persian_num(total_students),
        "total_students_raw": total_students
    }
    
    if total_students == 0:
        raise ValueError("No results available to generate report.")

    results_counts = {f"Q{i}": [0, 0, 0] for i in range(1, 15)}
    
    valid_forms = 0
    invalid_forms = 0

    for fr in form_results:
        if getattr(fr, 'valid', True):
            valid_forms += 1
        else:
            invalid_forms += 1

        answers = fr.answers()
        for i in range(14):
            if i >= len(answers):
                continue
            ans = answers[i]
            if ans == "Yes":
                results_counts[f"Q{i+1}"][0] += 1
            elif ans == "Somewhat":
                results_counts[f"Q{i+1}"][1] += 1
            elif ans == "No":
                results_counts[f"Q{i+1}"][2] += 1

    chart_data_positive = []
    chart_data_neutral = []
    chart_data_negative = []

    questions_info = {
        1: "آیا در آغاز سمستر کورس پالیسی تشریح گردیده است؟",
        2: "آیا تدریس مطابق کورس پالیسی صورت گرفته است؟",
        3: "آیا مواد درسی برای شما معرفی شده و موجود است؟",
        4: "آیا تدریس استاد قابل فهم است؟",
        5: "آیا از میتود تدریس استاد راضی هستید؟",
        6: "آیا استاد محصلان را در تدریس سهم میسازد؟",
        7: "آیا از سلوک و رویه اکادمیک استاد راضی هستید؟",
        8: "آیا استاد با پلان درسی منظم داخل صنف میشود؟",
        9: "آیا استاد به سوالات شما جواب قناعتبخش میدهد؟",
        10: "آیا استاد پابند به اصول، وقت و زمان معین میباشد؟",
        11: "(معکوس) آیا استاد به موضوعات غیرمرتبط تماس میگیرد؟",
        12: "آیا مشکلات درسی شما توسط استاد حل میگردد؟",
        13: "آیا از شیوههای ارزیابی استاد راضی هستید؟",
        14: "آیا استاد از تکنالوژی معلوماتی استفاده مینماید؟",
    }
    
    categories = [
        {"name": "۱. نصاب، پلانگذاری و مواد درسی", "q_nums": [1, 2, 3, 8]},
        {"name": "۲. میتودولوژی تدریس و تعامل صنف", "q_nums": [4, 5, 6, 9]},
        {"name": "۳. مدیریت صنف و مسلکی بودن", "q_nums": [7, 10, 11]},
        {"name": "۴. ارزیابی، تکنالوژی و حل مشکلات", "q_nums": [12, 13, 14]},
    ]
    
    table_data = []

    for key, values in results_counts.items():
        q_total = sum(values)
        if q_total == 0:
            yes_pct = partial_pct = no_pct = 0.0
        else:
            yes_pct = (values[0] / q_total) * 100
            partial_pct = (values[1] / q_total) * 100
            no_pct = (values[2] / q_total) * 100

        if key == "Q11":
            chart_data_positive.append(round(no_pct))
            chart_data_neutral.append(round(partial_pct))
            chart_data_negative.append(round(yes_pct))
        else:
            chart_data_positive.append(round(yes_pct))
            chart_data_neutral.append(round(partial_pct))
            chart_data_negative.append(round(no_pct))

    if chart_data_positive:
        overall_score = round(sum(chart_data_positive) / len(chart_data_positive))
    else:
        overall_score = 0

    all_questions_flat = []

    for cat in categories:
        cat_data = {"name": cat["name"], "questions": []}
        for q_num in cat["q_nums"]:
            q_key = f"Q{q_num}"
            vals = results_counts[q_key]
            q_total = sum(vals)
            yes_c, partial_c, no_c = vals
            
            if q_total == 0:
                y_p = p_p = n_p = 0
            else:
                y_p = round((yes_c / q_total) * 100)
                p_p = round((partial_c / q_total) * 100)
                n_p = round((no_c / q_total) * 100)
                
            if q_num == 11:
                green_pct, green_c = n_p, no_c
                yellow_pct, yellow_c = p_p, partial_c
                red_pct, red_c = y_p, yes_c
                suffix_green = " <br><small>(نخیر)</small>"
                short_text = questions_info[q_num].replace("(معکوس) ", "")
            else:
                green_pct, green_c = y_p, yes_c
                yellow_pct, yellow_c = p_p, partial_c
                red_pct, red_c = n_p, no_c
                suffix_green = ""
                short_text = questions_info[q_num]
                
            q_obj = {
                "num": to_persian_num(q_num),
                "text": questions_info[q_num] if q_num != 11 else f"<strong>(معکوس)</strong> {short_text}",
                "short_text": short_text,
                "green_text": f"{to_persian_num(green_pct)}٪ ({to_persian_num(green_c)}){suffix_green}",
                "yellow_text": f"{to_persian_num(yellow_pct)}٪ ({to_persian_num(yellow_c)})",
                "red_text": f"{to_persian_num(red_pct)}٪ ({to_persian_num(red_c)})",
                "green_bg": "bg-green" if green_pct > 0 else "",
                "yellow_bg": "bg-yellow" if yellow_pct > 0 else "",
                "red_bg": "bg-red" if red_pct > 0 else "",
                "raw_green_pct": green_pct,
                "raw_green_c": green_c,
                "raw_yellow_c": yellow_c,
                "raw_red_c": red_c
            }
            cat_data["questions"].append(q_obj)
            all_questions_flat.append(q_obj)
        table_data.append(cat_data)

    # 1. Radar Chart Data
    radar_labels = [cat["name"].split('. ')[1] for cat in categories]
    radar_data = []
    for cat in table_data:
        cat_pcts = [q["raw_green_pct"] for q in cat["questions"]]
        radar_data.append(round(sum(cat_pcts)/len(cat_pcts)) if cat_pcts else 0)

    # 2. Doughnut Chart (Overall Sentiments)
    total_green = sum(q["raw_green_c"] for q in all_questions_flat)
    total_yellow = sum(q["raw_yellow_c"] for q in all_questions_flat)
    total_red = sum(q["raw_red_c"] for q in all_questions_flat)

    # 3. Strengths and Weaknesses
    sorted_qs = sorted(all_questions_flat, key=lambda x: x["raw_green_pct"], reverse=True)
    top_3 = sorted_qs[:3]
    bottom_3 = sorted_qs[-3:][::-1] # Reverse so the absolute lowest is first

    # Get template directory from Config
    from config import Config
    template_dir = Config.TEMPLATES_DIR
    
    # Ensure template directory exists
    if not template_dir.exists():
        raise FileNotFoundError(f"Template directory not found: {template_dir}")
    
    env = Environment(loader=FileSystemLoader(str(template_dir)))
    env.filters['persian_num'] = to_persian_num
    
    template = env.get_template('qa_template.html')
    
    # Convert logos to base64 for embedding
    uni_logo_data = _image_to_base64(Config.DEFAULT_LOGO_PATH) if Config.DEFAULT_LOGO_PATH.exists() else ""
    mohe_logo_data = _image_to_base64(Config.QA_LOGO_PATH) if Config.QA_LOGO_PATH.exists() else ""

    html_output = template.render(
        meta=metadata,
        overall_score=to_persian_num(overall_score),
        positive_data=json.dumps(chart_data_positive),
        neutral_data=json.dumps(chart_data_neutral),
        negative_data=json.dumps(chart_data_negative),
        table_data=table_data,
        radar_labels=json.dumps(radar_labels),
        radar_data=json.dumps(radar_data),
        doughnut_data=json.dumps([total_green, total_yellow, total_red]),
        top_3=top_3,
        bottom_3=bottom_3,
        valid_forms=to_persian_num(valid_forms),
        invalid_forms=to_persian_num(invalid_forms),
        valid_forms_raw=valid_forms,
        invalid_forms_raw=invalid_forms,
        uni_logo_data=uni_logo_data,
        mohe_logo_data=mohe_logo_data
    )

    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write(html_output)

    return output_html_path
