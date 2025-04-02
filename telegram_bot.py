import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json

# Ma'lumotlarni saqlash uchun fayl nomi
DATA_FILE = "mahsulotlar_data.json"

# Ma'lumotlarni yuklash funksiyasi
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Ma'lumotlarni yuklashda xatolik: {e}")
            return []
    else:
        return []

# Ma'lumotlarni saqlash funksiyasi
def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        st.error(f"Ma'lumotlarni saqlashda xatolik: {e}")
        return False

# Dastur boshlanishi
def main():
    st.set_page_config(page_title="Mahsulot kirtish tizimi", page_icon="🛒")
    
    # Sahifa sarlavhasi
    st.title("🛒 Mahsulot ma'lumotlarini kiritish tizimi")
    
    # Ma'lumotlarni yuklash
    if 'mahsulotlar' not in st.session_state:
        st.session_state.mahsulotlar = load_data()
    
    # Tab yaratish
    tab1, tab2, tab3 = st.tabs(["📝 Mahsulot qo'shish", "🔍 Mahsulotlarni ko'rish", "📊 Hisobot olish"])
    
    with tab1:
        st.header("Yangi mahsulot qo'shish")
        
        with st.form("mahsulot_form"):
            mahsulot_nomi = st.text_input("Mahsulot nomi")
            mahsulot_narxi = st.number_input("Mahsulot narxi", min_value=0.0)
            
            # Bugungi sana
            sana = st.date_input("Sana", datetime.now())
            
            submitted = st.form_submit_button("Mahsulotni saqlash")
            
            if submitted:
                if mahsulot_nomi and mahsulot_narxi > 0:
                    # Yangi mahsulot ma'lumotlari
                    new_product = {
                        "nomi": mahsulot_nomi,
                        "narxi": mahsulot_narxi,
                        "sana": sana.strftime("%Y-%m-%d")
                    }
                    
                    # Mahsulotlar ro'yxatiga qo'shish
                    st.session_state.mahsulotlar.append(new_product)
                    
                    # Ma'lumotlarni saqlash
                    if save_data(st.session_state.mahsulotlar):
                        st.success(f"✅ Mahsulot qo'shildi: {mahsulot_nomi}, Narxi: {mahsulot_narxi}")
                    else:
                        st.error("Ma'lumotlarni saqlashda xatolik yuz berdi")
                else:
                    st.warning("Iltimos, barcha maydonlarni to'ldiring")
    
    with tab2:
        st.header("Mahsulotlar ro'yxati")
        
        if st.session_state.mahsulotlar:
            # Vaqt bo'yicha saralash imkoniyati
            sort_by_date = st.checkbox("Sana bo'yicha saralash")
            
            # Sana oralig'i filtri
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Boshlang'ich sana", datetime.now().replace(day=1))
            with col2:
                end_date = st.date_input("Tugash sanasi", datetime.now())
            
            # Ma'lumotlarni DataFrame ga o'tkazish
            df = pd.DataFrame(st.session_state.mahsulotlar)
            df['sana'] = pd.to_datetime(df['sana'])
            
            # Sana oralig'i bo'yicha filtrlash
            filtered_df = df[(df['sana'] >= pd.Timestamp(start_date)) & 
                             (df['sana'] <= pd.Timestamp(end_date))]
            
            # Sana bo'yicha saralash
            if sort_by_date:
                filtered_df = filtered_df.sort_values(by='sana')
            
            # Ma'lumotlarni ko'rsatish
            if not filtered_df.empty:
                # Ko'rsatish uchun formatlash
                display_df = filtered_df.copy()
                display_df['sana'] = display_df['sana'].dt.strftime('%Y-%m-%d')
                st.dataframe(display_df, use_container_width=True)
                
                # Tanlangan davr uchun umumiy summa
                total_sum = filtered_df['narxi'].sum()
                st.info(f"Umumiy summa: {total_sum:.2f}")
            else:
                st.info("Tanlangan davr oralig'ida ma'lumotlar mavjud emas")
            
            # Ma'lumotlarni tozalash imkoniyati
            if st.button("🗑️ Barcha ma'lumotlarni o'chirish", key="delete_all"):
                st.session_state.mahsulotlar = []
                save_data([])
                st.success("Barcha ma'lumotlar o'chirildi")
                st.experimental_rerun()
        else:
            st.info("Hozircha hech qanday ma'lumot kiritilmagan")
    
    with tab3:
        st.header("Hisobot")
        
        if st.session_state.mahsulotlar:
            # Ma'lumotlarni DataFrame ga o'tkazish
            df = pd.DataFrame(st.session_state.mahsulotlar)
            df['sana'] = pd.to_datetime(df['sana'])
            
            # Sana oralig'i tanlovi
            report_col1, report_col2 = st.columns(2)
            with report_col1:
                report_start_date = st.date_input("Hisobot: boshlang'ich sana", datetime.now().replace(day=1), key="report_start")
            with report_col2:
                report_end_date = st.date_input("Hisobot: tugash sanasi", datetime.now(), key="report_end")
            
            # Sana oralig'i bo'yicha filtrlash
            report_df = df[(df['sana'] >= pd.Timestamp(report_start_date)) & 
                          (df['sana'] <= pd.Timestamp(report_end_date))]
            
            if not report_df.empty:
                # Ko'rsatish uchun formatlash
                report_df_display = report_df.copy()
                report_df_display['sana'] = report_df_display['sana'].dt.strftime('%Y-%m-%d')
                
                # Excel ga yuklab olish
                @st.cache_data
                def convert_df_to_excel(df):
                    # DataFrame uchun fayl yaratish
                    output = pd.ExcelWriter(f"mahsulotlar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", engine='xlsxwriter')
                    df.to_excel(output, index=False, sheet_name='Mahsulotlar')
                    output.close()
                    
                    # Faylni bytega aylantirish
                    with open(output.path, 'rb') as f:
                        return f.read()
                
                # Mahsulotlar soni
                st.metric("Mahsulotlar soni", len(report_df))
                
                # Umumiy summa
                total_sum = report_df['narxi'].sum()
                st.metric("Umumiy summa", f"{total_sum:.2f}")
                
                # Excel ga eksport qilish
                excel_data = convert_df_to_excel(report_df_display)
                
                st.download_button(
                    label="📥 Excel fayl sifatida yuklab olish",
                    data=excel_data,
                    file_name=f"mahsulotlar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.ms-excel"
                )
            else:
                st.info("Tanlangan davr oralig'ida ma'lumotlar mavjud emas")
        else:
            st.info("Hisobot tayyorlash uchun avval ma'lumotlar kiriting")

if __name__ == "__main__":
    main()
