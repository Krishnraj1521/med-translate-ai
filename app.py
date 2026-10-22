                            "medical diagnosis, clinical advice, or treatment.",
                            "==================================================================",
                        ]
                    )
                    checklist_content = "\n".join(checklist_lines)
                    render_html("<div style='height: 8px;'></div>")
                    st.download_button(
                        label="📥 Download Doctor Questions Checklist (.txt)",
                        data=checklist_content,
                        file_name=f"medtranslate_doctor_checklist_{lang.lower()}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )
elif st.session_state.get("raw_response") and not analyze_clicked:
    with st.container():
        st.markdown("---")
        render_html('<div class="section-header">📋 Report Translation & Summary</div>')
        st.markdown(st.session_state["raw_response"])
# ================= 5. BOTTOM SECTION: MANDATORY MEDICAL DISCLAIMER =================
disclaimer_html = """
<div class="disclaimer-card">
    🔒 <strong>Mandatory Medical Disclaimer:</strong> MedTranslate AI is an informational tool created for 
    educational and communication assistance only. It is <strong>not</strong> a substitute for professional 
    medical diagnosis, advice, or treatment. Always consult a qualified, licensed healthcare provider 
    regarding any laboratory test results or underlying medical conditions.
</div>
"""
render_html(disclaimer_html)
