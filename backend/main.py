import os   # --- python 自带的 ，用来拼接文件路径的 ---
import traceback # --- python 自带的，用来把异常的堆栈转换成字符串 ---
from fastapi import FastAPI , Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
# --- 导入自己写的三组路由 --
from api import document_router, query_router, settings_router

# --创建一个 FastAPI 应用实例--
app = FastAPI(title="项目知识库", version='1.0.0')

# -- 告诉 FastAPI"任何没接住的异常都交给下面这个函数 --
@app.exeception_hander(Exception)
async def global_exeception_hander(request:Request,exe:Exception):
    tb = traceback.format_exception(type(exe),exe,exe.__traceback__)
    return JSONResponse(status_code=500,content={"detail": str(exc), "traceback": "".join(tb)})

# -- 注册CORS 中间件  --
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -- 注册路由 --
app.include_router(document_router)
app.include_router(query_router)
app.include_router(settings_router)

# -- 接口检查 --
@app.get("/api/health")
async def health():
    return {"status": "ok"}

# -- 
_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(_static_dir, "assets")), name="assets")

# -- 兜底路由  没有匹配到的就返回index.html --
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
        file_path = os.path.join(_static_dir, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(_static_dir, "index.html"))
