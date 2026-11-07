
import requests

from frontend.config import API_BASE_URL


class APIClient:

    def __init__(self):
        self.base_url = API_BASE_URL.rstrip("/")
        self.token = None

    def set_token(self, token: str):
        self.token = token

    def clear_token(self):
        self.token = None

    def _headers(self):
        headers = {}

        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        return headers

    def request(
        self,
        method: str,
        endpoint: str,
        timeout: int = 120,
        **kwargs
    ):
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self._headers(),
                timeout=timeout,
                **kwargs
            )

            try:
                data = response.json()
            except ValueError:
                data = {
                    "detail": response.text or "Invalid API response."
                }

            if not response.ok:
                if isinstance(data, dict):
                    message = data.get(
                        "detail",
                        "API request failed."
                    )
                else:
                    message = str(data)

                raise RuntimeError(
                    f"HTTP {response.status_code}: {message}"
                )

            return data

        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Cannot connect to FastAPI. Start the backend first."
            )

        except requests.exceptions.Timeout:
            raise RuntimeError(
                "The API request timed out. Please try again."
            )

        except requests.exceptions.RequestException as error:
            raise RuntimeError(f"Network error: {error}")

    # --------------------------------------------------
    # PUBLIC CAREERS PORTAL
    # --------------------------------------------------

    def get_public_jobs(self):
        return self.request(
            "GET",
            "/jobs/public"
        )

    def get_public_job(self, job_id: int):
        return self.request(
            "GET",
            f"/jobs/public/{job_id}"
        )

    def submit_public_application(
        self,
        job_id: int,
        full_name: str,
        email: str,
        phone: str,
        location: str,
        uploaded_file
    ):
        if uploaded_file is None:
            raise ValueError("Please select a resume.")

        if uploaded_file.size > 5 * 1024 * 1024:
            raise ValueError("Resume must not exceed 5 MB.")

        return self.request(
            "POST",
            f"/applications/public/{job_id}/apply",
            data={
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "location": location
            },
            files={
                "resume": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type or "application/octet-stream"
                )
            },
            timeout=120
        )

    # --------------------------------------------------
    # AUTHENTICATION
    # --------------------------------------------------

    def login(self, email: str, password: str):
        return self.request(
            "POST",
            "/auth/login",
            json={
                "email": email,
                "password": password
            }
        )

    def get_profile(self):
        return self.request(
            "GET",
            "/auth/me"
        )

    # --------------------------------------------------
    # JOB MANAGEMENT
    # --------------------------------------------------

    def get_jobs(self):
        return self.request(
            "GET",
            "/jobs/"
        )

    # --------------------------------------------------
    # RECRUITER RESUME UPLOAD
    # --------------------------------------------------

    def upload_candidate_resume(self, uploaded_file):

        if uploaded_file is None:
            raise ValueError("Please select a resume.")

        if uploaded_file.size > 5 * 1024 * 1024:
            raise ValueError("Resume size must not exceed 5 MB.")

        return self.request(
            "POST",
            "/resumes/recruiter-upload",
            files={
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type or "application/octet-stream"
                )
            },
            timeout=120
        )

    # --------------------------------------------------
    # AGENTIC AI CANDIDATE EVALUATION
    # --------------------------------------------------

    def evaluate_candidate(
        self,
        resume_text: str,
        job_title: str,
        job_description: str,
        candidate_experience_years: float | None = None,
        thread_id: str | None = None
    ):

        if not resume_text.strip():
            raise ValueError("Resume text cannot be empty.")

        if not job_title.strip():
            raise ValueError("Job title cannot be empty.")

        if not job_description.strip():
            raise ValueError("Job description cannot be empty.")

        payload = {
            "resume_text": resume_text,
            "job_title": job_title,
            "job_description": job_description,
            "candidate_experience_years": candidate_experience_years
        }

        if thread_id:
            payload["thread_id"] = thread_id

        return self.request(
            "POST",
            "/agentic/evaluate",
            json=payload,
            timeout=300
        )

    # --------------------------------------------------
    # HUMAN REVIEW AND APPROVAL
    # --------------------------------------------------

    def approve_evaluation(
        self,
        thread_id: str,
        approved: bool,
        comment: str = ""
    ):

        return self.request(
            "POST",
            "/agentic/approve",
            json={
                "thread_id": thread_id,
                "approved": approved,
                "comment": comment
            },
            timeout=120
        )

    # --------------------------------------------------
    # INTERVIEW INTELLIGENCE
    # --------------------------------------------------

    def generate_interview(
        self,
        job_title: str,
        job_description: str,
        candidate_skills: list[str],
        difficulty: str,
        question_count: int
    ):

        return self.request(
            "POST",
            "/interviews/generate",
            json={
                "job_title": job_title,
                "job_description": job_description,
                "candidate_skills": candidate_skills,
                "candidate_evidence": [],
                "difficulty": difficulty,
                "question_count": question_count
            },
            timeout=300
        )

    # --------------------------------------------------
    # RECRUITER MEMORY
    # --------------------------------------------------

    def get_memories(self):
        return self.request(
            "GET",
            "/agentic/memories"
        )

    def save_memory(
        self,
        memory_type: str,
        memory_key: str,
        memory_value: dict
    ):

        return self.request(
            "POST",
            "/agentic/memories",
            json={
                "memory_type": memory_type,
                "memory_key": memory_key,
                "memory_value": memory_value
            }
        )

    def delete_memory(
        self,
        memory_type: str,
        memory_key: str
    ):

        return self.request(
            "DELETE",
            f"/agentic/memories/{memory_type}/{memory_key}"
        )
