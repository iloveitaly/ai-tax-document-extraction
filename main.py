import io
import os
from typing import List, Optional

from celery import Celery, states
from celery.result import AsyncResult
from decouple import config
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine

DATABASE_URL = config("DATABASE_URL", default="sqlite:///./test.db")
CELERY_RESULT_BACKEND = DATABASE_URL
PORT = config("PORT", default=8000, cast=int)


class Folder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    files: List["FileRecord"] = Relationship(back_populates="folder")


class FileRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    content: bytes
    folder_id: Optional[int] = Field(default=None, foreign_key="folder.id")
    folder: Folder = Relationship(back_populates="files")


class PageAnalysis(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    page: int
    extraction_type: str
    folder_id: Optional[int] = Field(default=None, foreign_key="folder.id")
    folder: Folder = Relationship(back_populates="page_analysis")


app = FastAPI()

app.mount("/public", StaticFiles(directory="public"), name="public")

templates = Jinja2Templates(directory="templates")

engine = create_engine(DATABASE_URL)
celery_app = Celery("tasks", backend=CELERY_RESULT_BACKEND, broker=DATABASE_URL)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post("/upload/")
async def create_upload_files(files: list[UploadFile] = File(...)):
    async with Session(engine) as session:
        new_folder = Folder()
        session.add(new_folder)
        await session.flush()

        for file in files:
            data = await file.read()
            file_record = FileRecord(
                filename=file.filename, content=data, folder_id=new_folder.id
            )
            session.add(file_record)

        session.commit()

        task = celery_app.send_task("create_zip", args=[new_folder.id], kwargs={})
        return RedirectResponse(
            url=f"/success/{new_folder.id}?task_id={task.id}", status_code=303
        )


@app.get("/success/{folder_id}")
def success(request: Request, folder_id: int, task_id: str):
    return templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "folder_id": folder_id,
            "status_url": f"/status/{folder_id}?task_id={task_id}",
        },
    )


@app.get("/status/{folder_id}")
def check_status(request: Request, folder_id: int, task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    if task_result.state == states.SUCCESS:
        return RedirectResponse(url=f"/download-folder/{folder_id}?task_id={task_id}")
    else:
        return templates.TemplateResponse(
            "status.html", {"request": request, "task_state": task_result.state}
        )


@app.get("/download-folder/{folder_id}")
async def download_folder(folder_id: int, task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    if task_result.ready():
        zip_file_path = task_result.get()
        return FileResponse(zip_file_path, media_type="application/x-zip-compressed")
    raise HTTPException(status_code=404, detail="File not ready")


@celery_app.task(name="create_zip")
def create_zip(folder_id: int):
    with Session(engine) as session:
        folder = session.get(Folder, folder_id)
        if not folder:
            return None

        zip_file_path = f"temp/{folder_id}.zip"
        with io.BytesIO() as zip_buffer:
            with shutil.make_archive(
                zip_file_path, "zip", base_dir=str(folder_id)
            ) as archive:
                for file_record in folder.files:
                    archive.writestr(file_record.filename, file_record.content)
            zip_buffer.seek(0)
            with open(zip_file_path, "wb") as f:
                f.write(zip_buffer.getvalue())

        return zip_file_path


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=PORT)
