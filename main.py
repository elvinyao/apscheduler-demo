from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore

# Create a FastAPI app instance
app = FastAPI()

jobstores={
    'default': MemoryJobStore()
}

scheduler = AsyncIOScheduler(jobstores=jobstores,timezone='Asia/Tokyo')

@scheduler.scheduled_job('interval', seconds=10)
def scheduled_job_1():
    print("scheduled_job_1!")

@scheduler.scheduled_job('date', run_date='2025-02-02 22:34:00')
def scheduled_job_2():
    print("scheduled_job_2!")

@scheduler.scheduled_job('cron', day_of_week='mon-sun', hour=22, minute=35)
def scheduled_job_3():
    print("scheduled_job_3!")

@app.on_event("startup")
async def startup_event():
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()

@app.get("/")
async def read_root():
    return {"message": "Hello World"}