import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from supabase import Client, create_client


class SupabaseService:
    def __init__(self) -> None:
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
        self.bucket_name = os.getenv("SUPABASE_STORAGE_BUCKET", "generated-papers")
        self.client: Optional[Client] = None

        if self.url and self.key:
            self.client = create_client(self.url, self.key)
            self._ensure_bucket_exists()

    @property
    def is_configured(self) -> bool:
        return self.client is not None

    def _ensure_bucket_exists(self) -> None:
        if not self.client:
            return

        try:
            buckets = self.client.storage.list_buckets()
            bucket_ids = {bucket.get("id") for bucket in buckets or [] if isinstance(bucket, dict)}
            if self.bucket_name not in bucket_ids:
                self.client.storage.create_bucket(self.bucket_name, {"public": False})
        except Exception:
            # Bucket might already exist or current key might not have permissions.
            # We intentionally avoid crashing app startup.
            pass

    def save_generated_paper(
        self,
        owner_token: str,
        subject: str,
        semester: str,
        department: str,
        total_marks: int,
        paper_data: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None

        payload = {
            "owner_token": owner_token,
            "subject": subject,
            "semester": semester,
            "department": department,
            "total_marks": total_marks,
            "paper_data": paper_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            response = self.client.table("generated_papers").insert(payload).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception:
            try:
                legacy_payload = dict(payload)
                legacy_payload.pop("owner_token", None)
                legacy_payload["pc_number"] = owner_token
                response = self.client.table("generated_papers").insert(legacy_payload).execute()
                if response.data:
                    return response.data[0]
                return None
            except Exception:
                return None

    def update_paper_pdf_path(self, owner_token: str, paper_id: int, pdf_file_path: str) -> bool:
        if not self.client:
            return False

        payload = {"pdf_file_path": pdf_file_path}

        try:
            self.client.table("generated_papers").update(payload).eq("id", paper_id).eq("owner_token", owner_token).execute()
            return True
        except Exception:
            try:
                self.client.table("generated_papers").update(payload).eq("id", paper_id).eq("pc_number", owner_token).execute()
                return True
            except Exception:
                return False

    def upload_paper_pdf(self, owner_token: str, paper_id: int, filename: str, pdf_bytes: bytes) -> Optional[str]:
        if not self.client:
            return None

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        safe_filename = filename.replace(" ", "_")
        file_path = f"{owner_token}/{paper_id}/{timestamp}_{safe_filename}"

        try:
            self.client.storage.from_(self.bucket_name).upload(
                file=file_path,
                path=pdf_bytes,
                file_options={"content-type": "application/pdf", "upsert": "true"}
            )
            return file_path
        except Exception:
            try:
                self.client.storage.from_(self.bucket_name).upload(file_path, pdf_bytes, {"content-type": "application/pdf", "upsert": "true"})
                return file_path
            except Exception:
                return None

    def download_paper_pdf(self, pdf_file_path: str) -> Optional[bytes]:
        if not self.client:
            return None

        try:
            data = self.client.storage.from_(self.bucket_name).download(pdf_file_path)
            if isinstance(data, (bytes, bytearray)):
                return bytes(data)
            return None
        except Exception:
            return None

    def get_latest_paper_for_owner(self, owner_token: str) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None

        try:
            response = (
                self.client.table("generated_papers")
                .select("id, subject, semester, department, total_marks, paper_data, pdf_file_path, created_at")
                .eq("owner_token", owner_token)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
        except Exception:
            try:
                response = (
                    self.client.table("generated_papers")
                    .select("id, subject, semester, department, total_marks, paper_data, created_at")
                    .eq("owner_token", owner_token)
                    .order("created_at", desc=True)
                    .limit(1)
                    .execute()
                )
            except Exception:
                try:
                    response = (
                        self.client.table("generated_papers")
                        .select("id, subject, semester, department, total_marks, paper_data, pdf_file_path, created_at")
                        .eq("pc_number", owner_token)
                        .order("created_at", desc=True)
                        .limit(1)
                        .execute()
                    )
                except Exception:
                    try:
                        response = (
                            self.client.table("generated_papers")
                            .select("id, subject, semester, department, total_marks, paper_data, created_at")
                            .eq("pc_number", owner_token)
                            .order("created_at", desc=True)
                            .limit(1)
                            .execute()
                        )
                    except Exception:
                        return None

        if not response.data:
            return None

        return response.data[0]

    def get_papers_for_owner(self, owner_token: str, limit: int = 10) -> List[Dict[str, Any]]:
        if not self.client:
            return []

        try:
            response = (
                self.client.table("generated_papers")
                .select("id, subject, semester, department, total_marks, pdf_file_path, created_at")
                .eq("owner_token", owner_token)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data or []
        except Exception:
            try:
                response = (
                    self.client.table("generated_papers")
                    .select("id, subject, semester, department, total_marks, created_at")
                    .eq("owner_token", owner_token)
                    .order("created_at", desc=True)
                    .limit(limit)
                    .execute()
                )
                return response.data or []
            except Exception:
                try:
                    response = (
                        self.client.table("generated_papers")
                        .select("id, subject, semester, department, total_marks, pdf_file_path, created_at")
                        .eq("pc_number", owner_token)
                        .order("created_at", desc=True)
                        .limit(limit)
                        .execute()
                    )
                    return response.data or []
                except Exception:
                    try:
                        response = (
                            self.client.table("generated_papers")
                            .select("id, subject, semester, department, total_marks, created_at")
                            .eq("pc_number", owner_token)
                            .order("created_at", desc=True)
                            .limit(limit)
                            .execute()
                        )
                        return response.data or []
                    except Exception:
                        return []

    def get_paper_by_id_for_owner(self, owner_token: str, paper_id: int) -> Optional[Dict[str, Any]]:
        if not self.client:
            return None

        try:
            response = (
                self.client.table("generated_papers")
                .select("id, subject, semester, department, total_marks, paper_data, pdf_file_path, created_at")
                .eq("owner_token", owner_token)
                .eq("id", paper_id)
                .limit(1)
                .execute()
            )
            if response.data:
                return response.data[0]
        except Exception:
            try:
                response = (
                    self.client.table("generated_papers")
                    .select("id, subject, semester, department, total_marks, paper_data, created_at")
                    .eq("owner_token", owner_token)
                    .eq("id", paper_id)
                    .limit(1)
                    .execute()
                )
                if response.data:
                    return response.data[0]
            except Exception:
                pass

        try:
            response = (
                self.client.table("generated_papers")
                .select("id, subject, semester, department, total_marks, paper_data, pdf_file_path, created_at")
                .eq("pc_number", owner_token)
                .eq("id", paper_id)
                .limit(1)
                .execute()
            )
            if response.data:
                return response.data[0]
        except Exception:
            try:
                response = (
                    self.client.table("generated_papers")
                    .select("id, subject, semester, department, total_marks, paper_data, created_at")
                    .eq("pc_number", owner_token)
                    .eq("id", paper_id)
                    .limit(1)
                    .execute()
                )
                if response.data:
                    return response.data[0]
            except Exception:
                return None

        return None

    def save_feedback(
        self,
        name: str,
        department: str,
        prn: str,
        feedback: str,
    ) -> Dict[str, Any]:
        payload = {
            "name": name,
            "department": department,
            "prn": prn,
            "feedback": feedback,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        if not self.client:
            return {
                "success": False,
                "stored": "none",
                "message": "Supabase is not configured."
            }

        try:
            self.client.table("student_feedback").insert(payload).execute()
            return {
                "success": True,
                "stored": "supabase",
                "message": "Feedback submitted successfully."
            }
        except Exception as e:
            return {
                "success": False,
                "stored": "none",
                "message": f"Supabase feedback insert failed: {str(e)}"
            }

    def get_recent_feedback(self, limit: int = 6) -> List[Dict[str, Any]]:
        if not self.client:
            return []

        try:
            response = (
                self.client.table("student_feedback")
                .select("name, department, prn, feedback, created_at")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data or []
        except Exception:
            return []
