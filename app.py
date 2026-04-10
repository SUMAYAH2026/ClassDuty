import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(page_title="نظام الانتظار الذكي", layout="wide")

# السطر المعدل لتوسيط العنوان وضمان عمله على السحابة
st.markdown("<h1 style='text-align: center;'>🛡️ نظام إدارة حصص الانتظار المؤتمت</h1>", unsafe_allow_html=True)

# تنسيق بسيط لأداة رفع الملفات
col_f1, col_f2, col_f3 = st.columns([1, 2, 1])
with col_f2:
    uploaded_file = st.file_uploader("ارفعي ملف الجدول المدرسي (Excel)", type=["xlsx"])

if uploaded_file:
    # قراءة البيانات مع الحفاظ على أرقام الجوال كنصوص
    df = pd.read_excel(uploaded_file, dtype={'phone': str})
    
    col1, col2 = st.columns(2)
    with col1:
        absent_teacher = st.selectbox("اسم المعلمة الغائبة:", df['name'].unique())
    with col2:
        # مطابقة الاختصارات كما هي في ملفك
        day = st.selectbox("اليوم:", ["Sunday", "mon", "tus", "wed", "thr"])

    # جلب بيانات المعلمة الغائبة
    teacher_data = df[df['name'] == absent_teacher].iloc[0]
    
    # تحديد الحصص التي تحتاج تغطية
    absent_slots = [i for i in range(1, 8) if f"{day}_{i}" in df.columns and not pd.isna(teacher_data[f"{day}_{i}"])]
    
    st.info(f"المعلمة {absent_teacher} غائبة وعندها الحصص: {absent_slots}")

    if absent_slots:
        st.subheader("📍 توزيع الانتظار المقترح:")
        
        for slot in absent_slots:
            slot_column = f"{day}_{slot}"
            
            # المعلمات المتفرغات في هذه الحصة (الخلية فارغة في الإكسل)
            available = df[pd.isna(df[slot_column])].copy()
            available = available[available['name'] != absent_teacher].dropna(subset=['name'])
            
            qualified_candidates = []

            for index, teacher in available.iterrows():
                # 1. حساب إجمالي حصص المعلمة في اليوم (شرط الـ 5 حصص)
                daily_lessons = sum(1 for i in range(1, 8) if not pd.isna(teacher.get(f"{day}_{i}")))
                
                # 2. فحص الحصص المتتالية (شرط الـ 3 حصص)
                prev_slot = teacher.get(f"{day}_{slot-1}") if slot > 1 else None
                next_slot = teacher.get(f"{day}_{slot+1}") if slot < 7 else None
                # إذا كان لديها حصة قبل وحصة بعد الحالية، ستصبح 3 متتالية
                has_consecutive = not pd.isna(prev_slot) and not pd.isna(next_slot)

                # تطبيق الشروط الذكية
                if daily_lessons < 5 and not has_consecutive:
                    qualified_candidates.append({'data': teacher, 'total': daily_lessons})

            if qualified_candidates:
                # ترتيب المرشحات حسب النصاب الكلي (العدالة)
                qualified_candidates.sort(key=lambda x: x['data']['load'])
                selected = qualified_candidates[0]['data']
                count_h = qualified_candidates[0]['total']
                
                with st.expander(f"الحصة {slot} - الفصل: {teacher_data[slot_column]}"):
                    st.write(f"👤 **المعلمة المرشحة:** {selected['name']}")
                    st.write(f"📚 **حصصها الأصلية اليوم:** {int(count_h)}")
                    
                    phone_val = str(selected['phone']) if not pd.isna(selected['phone']) else ""
                    if phone_val:
                        # رسالة الواتساب
                        msg = f"السلام عليكم أ. {selected['name']}. لديك حصة انتظار الحصة {slot} في فصل {teacher_data[slot_column]} بدلا من {absent_teacher}."
                        encoded_msg = urllib.parse.quote(msg)
                        wa_link = f"https://wa.me/{phone_val}?text={encoded_msg}"
                        st.markdown(f"[📩 إرسال تنبيه واتساب]({wa_link})")
                    else:
                        st.warning("⚠️ لا يوجد رقم جوال مسجل لهذه المعلمة.")
            else:
                st.error(f"لا توجد معلمة تحقق الشروط للحصة {slot}!")