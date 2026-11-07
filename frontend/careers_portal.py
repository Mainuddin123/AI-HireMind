
import os
import html
from urllib.parse import urlencode

import streamlit as st


def get_careers_url(job_id=None):
    base_url = os.getenv(
        "PUBLIC_APP_URL",
        "http://localhost:8501"
    ).rstrip("/")

    params = {"careers": "1"}

    if job_id is not None:
        params["job_id"] = str(job_id)

    return f"{base_url}/?{urlencode(params)}"


def render_careers_portal(api):

    st.markdown(
        """
        <div style="text-align:center;padding:25px 0;">
            <h1 class="rainbow-title" style="font-size:42px;">
                🧠 AI HireMind Careers
            </h1>
            <p style="color:#aab8d2;font-size:17px;">
                Discover opportunities. Showcase your skills.
                Build your future.
            </p>
        </div>
        <div class="rainbow-line"></div>
        """,
        unsafe_allow_html=True
    )

    job_id = st.query_params.get("job_id")

    # --------------------------------------------------
    # INDIVIDUAL JOB DETAILS
    # --------------------------------------------------

    if job_id:

        try:
            job = api.get_public_job(int(job_id))

        except (ValueError, RuntimeError):
            st.error("This job is unavailable or no longer active.")

            if st.button("← Browse all jobs"):
                st.query_params.clear()
                st.query_params["careers"] = "1"
                st.rerun()

            return

        st.button(
            "← Browse all jobs",
            on_click=lambda: (
                st.query_params.clear(),
                st.query_params.update({"careers": "1"})
            )
        )

        st.markdown(
            f"""
            <div class="custom-card">
                <h2>{html.escape(job.get("title", "Job opportunity"))}</h2>
                <h4>{html.escape(job.get("company_name", ""))}</h4>
                <p class="muted-text">
                    📍 {html.escape(job.get("location", "Not specified"))}
                    &nbsp; | &nbsp;
                    {html.escape(job.get("employment_type", "Not specified"))}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        col1, col2 = st.columns(2)

        col1.metric(
            "Experience Required",
            f"{job.get('experience_required', 0)} years"
        )

        col2.metric(
            "Job ID",
            job.get("id", job_id)
        )

        st.markdown("### Job Description")
        st.write(job.get("description", ""))

        st.markdown("### Required Skills")

        for skill in job.get("required_skills") or []:
            st.markdown(
                f'<span class="skill-tag">{html.escape(str(skill))}</span>',
                unsafe_allow_html=True
            )

        preferred = job.get("preferred_skills") or []

        if preferred:
            st.markdown("### Preferred Skills")

            for skill in preferred:
                st.markdown(
                    f'<span class="skill-tag">{html.escape(str(skill))}</span>',
                    unsafe_allow_html=True
                )

        st.markdown('<div class="rainbow-line"></div>',
                    unsafe_allow_html=True)

        st.markdown("### Apply for this position")

        with st.form("public_job_application_form"):

            full_name = st.text_input(
                "Full name",
                max_chars=150
            )

            email = st.text_input(
                "Email address"
            )

            phone = st.text_input(
                "Phone number",
                max_chars=20
            )

            location = st.text_input(
                "Current location",
                max_chars=150
            )

            resume = st.file_uploader(
                "Upload resume (PDF, DOCX or TXT, maximum 5 MB)",
                type=["pdf", "docx", "txt"]
            )

            submitted = st.form_submit_button(
                "Submit Application",
                type="primary",
                use_container_width=True
            )

        if submitted:

            if not full_name.strip():
                st.warning("Please enter your full name.")

            elif not email.strip():
                st.warning("Please enter your email.")

            elif not phone.strip():
                st.warning("Please enter your phone number.")

            elif resume is None:
                st.warning("Please upload your resume.")

            else:
                try:
                    with st.spinner("Submitting your application..."):

                        result = api.submit_public_application(
                            job_id=int(job_id),
                            full_name=full_name.strip(),
                            email=email.strip(),
                            phone=phone.strip(),
                            location=location.strip(),
                            uploaded_file=resume
                        )

                    st.success(
                        "Your application has been submitted successfully!"
                    )

                    st.balloons()

                    st.markdown(
                        f"""
                        <div class="custom-card">
                            <h3>Application Confirmation</h3>
                            <p>Application ID:
                            <strong>{result.get("application_id")}</strong></p>
                            <p>Job ID:
                            <strong>{result.get("job_id")}</strong></p>
                            <p>Status:
                            <strong>{html.escape(result.get("status", "applied"))}</strong></p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                except Exception as error:
                    st.error(str(error))

        return

    # --------------------------------------------------
    # PUBLIC JOB LISTINGS
    # --------------------------------------------------

    st.markdown("### Explore Open Positions")

    try:
        jobs = api.get_public_jobs()

    except Exception as error:
        st.error(f"Unable to load jobs: {error}")
        return

    if not jobs:
        st.info("No active job openings are available right now.")
        return

    st.caption(f"{len(jobs)} active job opening(s)")

    for job in jobs:

        job_id = job.get("id")

        title = html.escape(str(job.get("title", "Job opportunity")))
        company = html.escape(str(job.get("company_name", "")))
        location = html.escape(str(job.get("location", "Not specified")))
        employment = html.escape(
            str(job.get("employment_type", "Not specified"))
        )

        skills = job.get("required_skills") or []

        skill_text = ", ".join(
            html.escape(str(skill)) for skill in skills
        )

        with st.container(border=True):

            st.markdown(
                f"""
                <h3>{title}</h3>
                <p style="color:#b9c7e5;">
                    {company} · {location} · {employment}
                </p>
                <p style="color:#aab8d2;">
                    Experience: {job.get("experience_required", 0)} years
                </p>
                <p style="color:#c4b5fd;">
                    Required skills: {skill_text}
                </p>
                """,
                unsafe_allow_html=True
            )

            col1, col2 = st.columns([1, 2])

            with col1:
                if st.button(
                    "View Details & Apply",
                    key=f"view_job_{job_id}",
                    type="primary",
                    use_container_width=True
                ):
                    st.query_params["careers"] = "1"
                    st.query_params["job_id"] = str(job_id)
                    st.rerun()

            with col2:
                share_url = get_careers_url(job_id)

                st.code(
                    share_url,
                    language=None
                )

    st.markdown('<div class="rainbow-line"></div>',
                unsafe_allow_html=True)

    st.caption(
        "AI HireMind Careers · Public recruitment portal"
    )
