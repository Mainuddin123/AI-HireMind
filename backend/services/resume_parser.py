
import re
from html import unescape

import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Users\mainu\Desktop\tesseract.exe"
)

SKILL_DICTIONARY = [
    "python", "java", "c++", "c", "javascript", "typescript",
    "sql", "mysql", "postgresql", "mongodb",
    "pandas", "numpy", "scikit-learn", "matplotlib",
    "machine learning", "deep learning", "artificial intelligence",
    "natural language processing", "computer vision",
    "tensorflow", "pytorch", "keras",
    "fastapi", "flask", "django", "streamlit",
    "langchain", "langgraph", "rag", "llm",
    "power bi", "tableau", "excel",
    "git", "github", "docker", "kubernetes",
    "kafka", "aws", "azure", "gcp",
    "html", "css", "react", "node.js",
    "rest api", "data analysis", "data visualization",
    "statistics", "data structures", "algorithms"
]

EDUCATION_KEYWORDS = [
    "b.tech", "bachelor of technology",
    "b.e", "bachelor of engineering",
    "b.sc", "bachelor of science",
    "m.tech", "master of technology",
    "m.sc", "master of science",
    "mba", "mca", "ph.d",
    "intermediate", "higher secondary",
    "ssc", "10th", "12th",
    "computer science", "data science"
]

INDIAN_STATES = [
    "andhra pradesh", "arunachal pradesh", "assam",
    "bihar", "chhattisgarh", "goa", "gujarat",
    "haryana", "himachal pradesh", "jharkhand",
    "karnataka", "kerala", "madhya pradesh",
    "maharashtra", "manipur", "meghalaya", "mizoram",
    "nagaland", "odisha", "punjab", "rajasthan",
    "sikkim", "tamil nadu", "telangana", "tripura",
    "uttar pradesh", "uttarakhand", "west bengal",
    "delhi", "jammu and kashmir", "ladakh"
]

INDIAN_CITIES = [
    "hyderabad", "visakhapatnam", "vijayawada",
    "guntur", "nellore", "tirupati", "kurnool",
    "warangal", "karimnagar", "nizamabad",
    "bangalore", "bengaluru", "chennai", "mumbai",
    "pune", "delhi", "new delhi", "kolkata",
    "kochi", "thiruvananthapuram", "mysore",
    "mysuru", "coimbatore", "madurai", "ahmedabad",
    "surat", "jaipur", "lucknow", "noida",
    "gurugram", "gurgaon", "faridabad",
    "bhopal", "indore", "patna", "ranchi",
    "bhubaneswar", "chandigarh", "dehradun"
]


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = unescape(text)
    text = text.replace("\x00", " ")
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    return text


def extract_image_text(image_path: str) -> str:
    try:
        with Image.open(image_path) as image:
            image = image.convert("RGB")
            extracted_text = pytesseract.image_to_string(
                image,
                lang="eng"
            )

        return normalize_text(extracted_text)

    except Exception as error:
        raise RuntimeError(
            f"Image OCR extraction failed: {error}"
        ) from error


def extract_email(text: str) -> str | None:
    pattern = (
        r"(?<![A-Za-z0-9._%+-])"
        r"[A-Za-z0-9._%+-]+"
        r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"
        r"(?![A-Za-z0-9.-])"
    )

    matches = re.findall(pattern, text)

    if not matches:
        return None

    return matches[0].lower()


def extract_phone(text: str) -> str | None:
    patterns = [
        r"(?<!\d)(?:\+91[\s.-]?)?[6-9]\d{9}(?!\d)",
        r"(?<!\d)\+\d{1,3}[\s.-]?"
        r"(?:\(?\d{2,5}\)?[\s.-]?){1,3}\d{3,8}(?!\d)"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return re.sub(
                r"\s+",
                " ",
                match.group(0).strip()
            )

    return None


def extract_location(text: str) -> str | None:
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    label_pattern = re.compile(
        r"(?i)^\s*(?:current\s+location|"
        r"location|city|address|based\s+in|"
        r"residing\s+in|present\s+address)"
        r"\s*[:\-]\s*(.+)$"
    )

    for line in lines:
        match = label_pattern.search(line)

        if match:
            location = match.group(1).strip()

            location = re.split(
                r"\s{2,}|\||;",
                location
            )[0].strip()

            location = re.sub(
                r"\s+(?:phone|mobile|email|linkedin|github)\s*[:\-].*$",
                "",
                location,
                flags=re.IGNORECASE
            ).strip()

            if 2 <= len(location) <= 120:
                return location

    for line in lines[:15]:
        normalized_line = line.lower()

        for city in sorted(INDIAN_CITIES, key=len, reverse=True):
            city_pattern = (
                r"(?<![a-z])"
                + re.escape(city)
                + r"(?![a-z])"
            )

            city_match = re.search(
                city_pattern,
                normalized_line
            )

            if not city_match:
                continue

            start = city_match.start()
            end = city_match.end()
            remaining = normalized_line[end:]

            for state in sorted(
                INDIAN_STATES,
                key=len,
                reverse=True
            ):
                state_pattern = (
                    r"^\s*,?\s*"
                    + re.escape(state)
                    + r"(?![a-z])"
                )

                state_match = re.match(
                    state_pattern,
                    remaining
                )

                if state_match:
                    end += state_match.end()
                    break

            location = line[start:end].strip(" ,|-")

            if location:
                return location

    for line in lines[:15]:
        for state in sorted(
            INDIAN_STATES,
            key=len,
            reverse=True
        ):
            state_pattern = (
                r"(?<![a-z])"
                + re.escape(state)
                + r"(?![a-z])"
            )

            state_match = re.search(
                state_pattern,
                line,
                re.IGNORECASE
            )

            if state_match and len(line) <= 120:
                return line.strip()

    return None


def extract_name(text: str) -> str | None:
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return None

    ignored_phrases = [
        "resume", "curriculum vitae", "contact",
        "profile", "professional summary",
        "career objective", "objective", "education",
        "experience", "skills", "technical skills",
        "projects", "certifications", "email",
        "phone", "mobile", "address", "linkedin",
        "github", "portfolio", "developer",
        "engineer", "data scientist",
        "artificial intelligence"
    ]

    for line in lines[:10]:
        lower_line = line.lower()

        if "@" in line:
            continue

        if "http://" in lower_line or "https://" in lower_line:
            continue

        if re.search(r"\d{7,}", line):
            continue

        cleaned = re.sub(
            r"(?i)^(name|candidate name)\s*[:\-]\s*",
            "",
            line
        )

        cleaned = re.sub(
            r"[^A-Za-z\s.'-]",
            "",
            cleaned
        ).strip()

        if not cleaned:
            continue

        words = cleaned.split()

        if not 2 <= len(words) <= 5:
            continue

        if len(cleaned) > 70:
            continue

        if any(
            phrase in cleaned.lower()
            for phrase in ignored_phrases
        ):
            continue

        if any(len(word) < 2 for word in words):
            continue

        if cleaned.isupper() and len(words) == 1:
            continue

        return cleaned

    return None


def extract_candidate_details(text: str) -> dict:
    return {
        "full_name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "location": extract_location(text)
    }


def extract_skills(text: str) -> list[str]:
    normalized_text = text.lower()
    found_skills = []

    for skill in SKILL_DICTIONARY:
        pattern = (
            r"(?<![a-zA-Z0-9+#.])"
            + re.escape(skill)
            + r"(?![a-zA-Z0-9+#.])"
        )

        if re.search(pattern, normalized_text):
            found_skills.append(skill)

    return sorted(set(found_skills))


def extract_experience(text: str) -> float | None:
    patterns = [
        r"(\d+(?:\.\d+)?)\+?\s*years?\s+(?:of\s+)?experience",
        r"experience\s*[:\-]?\s*(\d+(?:\.\d+)?)\+?\s*years?",
        r"(\d+(?:\.\d+)?)\+?\s*yrs?\s+experience"
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            try:
                years = float(match.group(1))

                if 0 <= years <= 60:
                    return years

            except ValueError:
                continue

    return None


def extract_education(text: str) -> list[str]:
    education = []

    for line in text.splitlines():
        cleaned_line = line.strip()

        if not cleaned_line:
            continue

        lower_line = cleaned_line.lower()

        if any(
            keyword in lower_line
            for keyword in EDUCATION_KEYWORDS
        ):
            education.append(cleaned_line[:250])

    return list(dict.fromkeys(education))[:10]


def analyze_resume(text: str) -> dict:
    text = normalize_text(text)
    candidate_details = extract_candidate_details(text)

    return {
        "full_name": candidate_details["full_name"],
        "email": candidate_details["email"],
        "phone": candidate_details["phone"],
        "location": candidate_details["location"],
        "skills": extract_skills(text),
        "experience_years": extract_experience(text),
        "education": extract_education(text)
    }
