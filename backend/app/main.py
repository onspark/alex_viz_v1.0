from fastapi import FastAPI, APIRouter, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware import Middleware

from app.components.operator import Operator

from app.schemas import UserInput

from app.app_settings import Settings
from app.logger import logger

from app.utils import save_json


settings = Settings()
VERSION = settings.VERSION

app = FastAPI(title="ALEX Argumentation-based Legal EXplanation System",
              description="API for Legal Explanations", version=VERSION)

api_router = APIRouter(prefix=f"/api/v{VERSION}")

origins = [
    "*"
]

# if settings.BACKEND_CORS_ORIGINS:
app.add_middleware(
    CORSMiddleware,
    # allow_origins=[str(origin)
    #                for origin in settings.BACKEND_CORS_ORIGINS],
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# default route
@app.get("/", status_code=200)  
def root(request: Request):
    logger.info(f"API running at /api/v{VERSION}/")
    
# TODO: Implement asynchrounous processing for better task execution
@api_router.post("/alex_viz", status_code=200)
def run_alex(input_data:UserInput):
    # logger.info(f"Received input data: {input_data.arguments}")
    logger.info(f"User action: {input_data.action_option}")
    operator = Operator(input_data)
    operator.run()
    alex_result = operator.result
    
    file_name_prefix = "GENERATE" if input_data.action_option > 2 else "INIT"
    save_json(data=alex_result, file_name_prefix = file_name_prefix)
    logger.info(f"Result saved to file: {file_name_prefix}.json")
    
    result = {}
    result['success'] = True
    result['crime_fact'] = input_data.crime_fact
    result['data'] = alex_result
    return result


app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")