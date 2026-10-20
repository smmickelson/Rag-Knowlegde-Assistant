import streamlit as st

st.title("Networking Assessment: Hello World")
st.write("If you can read this, the deploy works.")

score = st.slider("Test input", 1, 4, 2)
if st.button("Run"):
    st.metric("Echoed score", score)