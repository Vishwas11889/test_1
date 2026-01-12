import streamlit as st
# import openai
import os
import json
from langchain_groq import ChatGroq



# openai.api_key = "YOUR_API_KEY"

SYSTEM_PROMPT = """
You are a clinical documentation and ICD-10 coding assistant for Indian hospitals.

TASK:
1. Structure doctor free-text notes into clinical sections.
2. Suggest ICD-10 codes ONLY if diagnosis is clearly mentioned.
3. Do NOT assume diagnoses.
4. Provide at most 3 ICD codes.
5. Include confidence (High / Medium / Low).

If diagnosis is unclear, keep ICD list empty.

Return STRICT JSON ONLY in the following structure:

{
  "patient_summary": {
    "chief_complaint": "",
    "duration": ""
  },
  "clinical_findings": {
    "vitals": "",
    "examination": ""
  },
  "diagnosis": {
    "provisional": "",
    "final": ""
  },
  "icd_codes": [
    {
      "code": "",
      "description": "",
      "confidence": ""
    }
  ],
  "medications": [
    {
      "name": "",
      "dose": "",
      "frequency": "",
      "duration": ""
    }
  ],
  "advice": {
    "general": "",
    "diet": "",
    "activity": ""
  },
  "follow_up": {
    "review_after": "",
    "warning_signs": ""
  },
  "discharge_summary": {
    "reason_for_admission": "",
    "hospital_course": "",
    "condition_at_discharge": "",
    "discharge_medications": "",
    "follow_up_plan": ""
  }
}
"""

st.set_page_config(page_title="Doctor Documentation", layout="wide")
st.title("🩺 Clinical Documentation ")

api_key = os.environ("api_key")

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    max_tokens=None,
    reasoning_format="parsed",
    timeout=None,
    max_retries=2,
    api_key=api_key
    # other params...
)
structured_llm = llm.with_structured_output(method="json_mode", include_raw=True)


doctor_text = st.text_area(
    "Doctor writes prescription / consultation / discharge notes:",
    height=230,
    placeholder="""
16 year female with fever since 3 days.
BP 110/70.
Diagnosis: viral fever.
Paracetamol 650 mg BD for 3 days.
Advised fluids and rest.
Review after 2 days.
"""
)

if st.button("Generate "):
    if not doctor_text.strip():
        st.warning("Please enter clinical notes")
    # if not api_key:
    #     st.warning("Please enter API key")
    #     st.stop()

    else:
        with st.spinner("Processing..."):
            # response = openai.ChatCompletion.create(
            #     model="gpt-4o-mini",
            #     temperature=0,
            #     messages=[
            #         {"role": "system", "content": SYSTEM_PROMPT},
            #         {"role": "user", "content": doctor_text}
            #     ]
            # )

            messages = [
    (
        "system",
        SYSTEM_PROMPT,
    ),
    ("human",  doctor_text),
]
            response = structured_llm.invoke(messages)
            # ai_msg
            # response = structured_llm
            try:
                print(response["raw"].content)
                data = json.loads(response["raw"].content)

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("🧾 Consultation")
                    st.write("**Chief Complaint:**", data["patient_summary"]["chief_complaint"])
                    st.write("**Duration:**", data["patient_summary"]["duration"])
                    st.write("**Vitals:**", data["clinical_findings"]["vitals"])
                    st.write("**Diagnosis:**", data["diagnosis"]["final"])

                    st.subheader("🏷 ICD-10 Suggestions")
                    if data["icd_codes"]:
                        for icd in data["icd_codes"]:
                            st.write(
                                f"- **{icd['code']}** – {icd['description']} "
                                f"(Confidence: {icd['confidence']})"
                            )
                    else:
                        st.info("No ICD code suggested (diagnosis unclear)")

                with col2:
                    st.subheader("💊 Medications")
                    for med in data["medications"]:
                        st.write(
                            f"- {med['name']} | {med['dose']} | {med['frequency']} | {med['duration']}"
                        )

                    st.subheader("📌 Advice")
                    st.write(data["advice"]["general"])
                    st.write(data["advice"]["diet"])
                    st.write(data["advice"]["activity"])

                    st.subheader("🔁 Follow-Up")
                    st.write(data["follow_up"]["review_after"])
                    st.write(data["follow_up"]["warning_signs"])

                st.subheader("🏥 Discharge Summary (Auto)")
                st.json(data["discharge_summary"])

            except Exception:
                st.error("Failed to parse AI response")
                st.text(response.choices[0].message.content)
