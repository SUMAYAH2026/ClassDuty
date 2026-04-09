import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(page_title="نظام الانتظار الذكي", layout="wide")
st.title("🛡️ نظام إدارة حصص الانتظار المؤتمت")

# رفع ملف البيانات
uploaded_file = st.file_uploader("ارفعي ملف الجدول المدرسي (Excel)", type=["xlsx"])

if uploaded_file:
    # قراءة الملف مع التأكد من قراءة أرقام الجوال كنصوص
    df = pd.read_excel(uploaded_file, dtype={'phone': str})
    
    col1, col2 = st.columns(2)
    with col1:
        absent_teacher = st.selectbox("اسم المعلمة الغائبة:", df['name'].unique())
    with col2:
        # مطابقة الاختصارات في الإكسل الخاص بك
        day = st.selectbox("اليوم:", ["Sunday", "mon", "tus", "wed", "thr"])

    # تحديد بيانات المعلمة الغائبة
    teacher_data = df[df['name'] == absent_teacher].iloc[0]
    
    # البحث عن الحصص التي بها بيانات (فصول)
    absent_slots = []
    for i in range(1, 8):
        column_name = f"{day}_{i}"
        if column_name in df.columns:
            if not pd.isna(teacher_data[column_name]):
                absent_slots.append(i)
    
    st.info(f"المعلمة {absent_teacher} غائبة وعندها الحصص: {absent_slots}")

    if absent_slots:
        st.subheader("📍 توزيع الانتظار المقترح:")
        
        for slot in absent_slots:
            slot_column = f"{day}_{slot}"
            duty_column = f"{day}_duty" 
            
            # البحث عن البديلات المتفرغات
            available = df[pd.isna(df[slot_column])]
            available = available[available['name'] != absent_teacher]
            available = available.dropna(subset=['name'])
            
            if not available.empty:
                # ترتيب حسب النصاب واستبعاد المناوبات
                if duty_column in df.columns:
                    no_duty = available[available[duty_column] != 1]
                    candidates = no_duty.sort_values(by='load') if not no_duty.empty else available.sort_values(by='load')
                else:
                    candidates = available.sort_values(by='load')
                
                selected = candidates.iloc[0]
                
                # عرض النتائج في صناديق منسدلة
                with st.expander(f"الحصة {slot} - الفصل: {teacher_data[slot_column]}"):
                    st.write(f"👤 **المعلمة المرشحة:** {selected['name']}")
                    st.write(f"📚 **النصاب الحالي:** {selected['load']}")
                    
                    phone_val = str(selected['phone']) if not pd.isna(selected['phone']) else ""
                    
                    if phone_val:
                        # رسالة الواتساب مصححة بالكامل لتجنب أخطاء الأقواس
                        msg = f"السلام عليكم أ. {selected['name']}. لديك حصة انتظار الحصة {slot} في فصل {teacher_data[slot_column]} بدلا من الزميلة {absent_teacher}."
                        encoded_msg = urllib.parse.quote(msg)
                        wa_link = f"https://wa.me/{phone_val}?text={encoded_msg}"
                        st.markdown(f"[📩 إرسال تنبيه واتساب]({wa_link})")
                    else:
                        st.warning("⚠️ لا يوجد رقم جوال مسجل لهذه المعلمة.")
            else:
                st.error(f"لا توجد معلمة متفرغة في الحصة {slot}!")