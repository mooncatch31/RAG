from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Integer, ForeignKey, JSON, Index, CheckConstraint, func
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from datetime import datetime
import uuid

class Base(DeclarativeBase):
    pass

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True, default="default")
    filename: Mapped[str] = mapped_column(String(512))
    mime: Mapped[str] = mapped_column(String(128))
    bytes: Mapped[int] = mapped_column(Integer)
    storage_uri: Mapped[str] = mapped_column(String(1024))
    file_sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(16), default="uploaded")  # uploaded|processed|failed
    meta: Mapped[dict | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    __table_args__ = (
        CheckConstraint("status in ('uploaded','processed','failed')", name="documents_status_chk"),
        Index("ix_documents_workspace_status", "workspace_id", "status"),
    )

class Chunk(Base):
    __tablename__ = "chunks"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    idx: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    page_start: Mapped[int | None] = mapped_column(Integer, default=None)
    page_end: Mapped[int | None] = mapped_column(Integer, default=None)
    token_count: Mapped[int] = mapped_column(Integer, default=0)
    sha256: Mapped[str | None] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    document: Mapped["Document"] = relationship(back_populates="chunks")
    __table_args__ = (Index("ix_chunks_doc_idx", "document_id", "idx", unique=True),)

class Query(Base):
    __tablename__ = "queries"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True, default="default")
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str | None] = mapped_column(Text, default=None)
    confidence: Mapped[float | None] = mapped_column()
    missing_info: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)
    suggested_enrichment: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=None)
    used_chunk_ids: Mapped[list[uuid.UUID] | None] = mapped_column(ARRAY(UUID(as_uuid=True)), default=None)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    __table_args__ = (Index("ix_queries_workspace_created", "workspace_id", "created_at"),)

class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("queries.id", ondelete="CASCADE"), index=True)
    rating: Mapped[int] = mapped_column()
    comment: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    
class DocumentReputation(Base):
    __tablename__ = "document_reputation"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[str] = mapped_column(String(64), index=True, default="default")
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    up_count: Mapped[int] = mapped_column(Integer, default=0)
    down_count: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column()  # smoothed reputation
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
    __table_args__ = (Index("ix_docrep_ws_doc", "workspace_id", "document_id", unique=True),)
