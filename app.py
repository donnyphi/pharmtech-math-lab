import streamlit as st

st.set_page_config(page_title="PharmTech Math Lab", page_icon="💊")

st.title("PharmTech Math Lab")
st.write("A practice tool for pharmacy technician math.")

st.warning("Educational practice only. Not for clinical decision-making.")

st.header("Dose to Volume Calculator")

dose_mg = st.number_input("Ordered dose (mg)", min_value=0.0)
strength_mg = st.number_input("Medication strength (mg)", min_value=0.0)
volume_ml = st.number_input("Strength volume (mL)", min_value=0.0)

if st.button("Calculate"):
    if strength_mg <= 0 or volume_ml <= 0:
        st.error("Strength and volume must be greater than 0.")
    else:
        concentration = strength_mg / volume_ml
        answer = dose_mg / concentration

        st.success(f"Draw up {answer:.2f} mL")
        st.write(f"Concentration = {strength_mg} mg / {volume_ml} mL = {concentration:.2f} mg/mL")
        st.write(f"Volume = {dose_mg} mg ÷ {concentration:.2f} mg/mL = {answer:.2f} mL")
