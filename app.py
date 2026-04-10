import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(page_title="نظام الانتظار الذكي", layout="wide")

# محاذاة العنوان والرفع إلى الوسط باستخدام CSS
st.markdown("""
    <style>
    .main { text-align: center; }
    .stSelectbox, .stFileUploader { width: 80%; margin: 0 auto; }
    h1 { text-align: center; color: #4A90E2; }
    </style>
    """, unsafe_all_original_headers=True)

st.title("🛡️ نظام إدارة حصص الانتظار المؤتمت")

uploaded_file = st.file_uploader("ارفعي ملف الجدول المدرسي (Excel)", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, dtype={'phone': str})
    
    col1, col2 = st.columns(2)
    with col1:
        absent_teacher = st.selectbox("اسم المعلمة الغائبة:", df['name'].unique())
    with col2:
        day = st.selectbox("اليوم:", ["Sunday", "mon", "tus", "wed", "thr"])

    teacher_data = df[df['name'] == absent_teacher].iloc[0]
    
    # تحديد الحصص التي غابت عنها المعلمة
    absent_slots = [i for i in range(1, 8) if f"{day}_{i}" in df.columns and not pd.isna(teacher_data[f"{day}_{i}"])]
    
    st.info(f"المعلمة {absent_teacher} غائبة وعندها الحصص: {absent_slots}")

    if absent_slots:
        st.subheader("📍 توزيع الانتظار المقترح:")
        
        for slot in absent_slots:
            slot_column = f"{day}_{slot}"
            
            # 1. المعلمات المتفرغات في هذه الحصة
            available = df[pd.isna(df[slot_column])].copy()
            available = available[available['name'] != absent_teacher].dropna(subset=['name'])
            
            qualified_candidates = []

            for index, teacher in available.iterrows():
                # حساب إجمالي حصص المعلمة في هذا اليوم (شرط الـ 5 حصص)
                daily_lessons = 0
                for i in range(1, 8):
                    if not pd.isna(teacher.get(f"{day}_{i}")):
                        daily_lessons += 1
                
                # فحص الحصص المتتالية (شرط الـ 3 حصص متتالية)
                # نفحص الحصة السابقة والحصة التالية للحصة الحالية
                has_consecutive = False
                prev_slot = teacher.get(f"{day}_{slot-1}") if slot > 1 else None
                next_slot = teacher.get(f"{day}_{slot+1}") if slot < 7 else None
                
                # إذا كانت الحصة السابقة والحصة التالية مشغولتين، يعني ستصبح 3 حصص متتالية
                if not pd.isna(prev_slot) and not pd.isna(next_slot):
                    has_consecutive = True

                # تطبيق الشروط الجديدة
                if daily_lessons < 5 and not has_consecutive:
                    # إضافة المعلمة مع تسجيل نصابها الحالي للمقارنة
                    qualified_candidates.append(teacher)

            if qualified_candidates:
                # تحويل النتائج إلى DataFrame لترتيبهم حسب النصاب (العدالة)
                final_df = pd.DataFrame(qualified_candidates)
                selected = final_df.sort_values(by='load').iloc[0]
                
                with st.expander(f"الحصة {slot} - الفصل: {teacher_data[slot_column]}"):
                    st.write(f"👤 **المعلمة المرشحة:** {selected['name']}")
                    st.write(f"📚 **مجموع حصصها اليوم:** {int(daily_lessons)}")
                    
                    phone_val = str(selected['phone']) if not pd.isna(selected['phone']) else ""
                    if phone_val:
                        msg = f"السلام عليكم أ. {selected['name']}. لديك حصة انتظار الحصة {slot} في فصل {teacher_data[slot_column]} بدلا من {absent_teacher}."
                        encoded_msg = urllib.parse.quote(msg)
                        wa_link = f"https://wa.me/{phone_val}?text={encoded_msg}"
                        st.markdown(f"[📩 إرسال تنبيه واتساب]({wa_link})")
            else:
                st.error(f"لا توجد معلمة تحقق الشروط للحصة {slot}!")