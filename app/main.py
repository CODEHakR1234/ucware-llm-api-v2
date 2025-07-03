# main.py

import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from app.controller import pdf_summary_controller, chat_summary_controller

app = FastAPI(title="Multi-Summary API")
app.include_router(pdf_summary_controller.router)
app.include_router(chat_summary_controller.router)

