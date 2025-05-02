from datetime import datetime
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
from src.models import Report
from contextlib import asynccontextmanager
from typing import Optional
from src.database import AsyncSessionLocal

class ReportService:
    def __init__(self):
        # Cache for frequently accessed reports
        self._report_cache = {}
        # Track recently updated reports to minimize refreshes
        self._recently_updated = set()

    @asynccontextmanager
    async def _ensure_session(self, db: Optional[AsyncSession] = None):
        """Helper to manage session lifecycle"""
        if db is not None:
            yield db
        else:
            async with AsyncSessionLocal() as new_db:
                yield new_db
                await new_db.commit()

    async def create_report(self, image_file: UploadFile, db: Optional[AsyncSession] = None) -> Report:
        async with self._ensure_session(db) as session:
            report = Report(
                filename=image_file.filename,
                format=image_file.content_type,
                received_time=datetime.now(),
                model_time_seconds=0.0,
                body_part="",
                confidence=0.0,
                prediction="",
                fracture_confidence=0.0,
                status="In Progress",
                error=''
            )
            session.add(report)
            await session.commit()
            await session.refresh(report)
            self._report_cache[report.id] = report
            return report

    async def fetch_report_by_id(self, report_id: UUID, db: Optional[AsyncSession] = None) -> Optional[Report]:
        # Check cache first
        if report_id in self._report_cache and report_id not in self._recently_updated:
            return self._report_cache[report_id]

        async with self._ensure_session(db) as session:
            result = await session.execute(
                select(Report)
                .where(Report.id == report_id)
                .execution_options(populate_existing=True)
            )
            report = result.scalar_one_or_none()
            
            if report:
                self._report_cache[report_id] = report
                self._recently_updated.discard(report_id)
            
            return report

    async def update_report(self, report: Report, db: Optional[AsyncSession] = None) -> None:
        async with self._ensure_session(db) as session:
            # Merge if report came from different session ,reason behind (because when try to update with background task sometimes it failed to track the report)
            if report not in session:
                report = await session.merge(report)
            
            self._recently_updated.add(report.id)
            await session.commit()
            
            # Only refresh if absolutely necessary
            if report.id in self._report_cache:
                await session.refresh(report)
                self._report_cache[report.id] = report

    async def bulk_create_reports(self, image_files: list[UploadFile], db: Optional[AsyncSession] = None) -> list[Report]:
        async with self._ensure_session(db) as session:
            reports = [
                Report(
                    filename=file.filename,
                    format=file.content_type,
                    received_time=datetime.now(),
                    model_time_seconds=0.0,
                    body_part="",
                    confidence=0.0,
                    prediction="",
                    fracture_confidence=0.0,
                    status="In Progress",
                    error=''
                )
                for file in image_files
            ]
            session.add_all(reports)
            await session.commit()
            
            for report in reports:
                await session.refresh(report)
                self._report_cache[report.id] = report
            
            return reports