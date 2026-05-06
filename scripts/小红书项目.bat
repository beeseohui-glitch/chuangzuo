@echo off
echo ==============================================
echo          一键启动 AI 开发环境
echo ==============================================
echo.

:: 1. 进入D盘
D:

:: 2. 进入项目目录
cd D:\chuangzuo

:: 3. 激活虚拟环境
call .\venv\Scripts\activate

:: 4. 启动 Docker 服务
docker-compose up -d

:: 5. 启动 Claude（跳过权限）
claude --dangerously-skip-permissions

echo.
echo ==============================
echo      环境启动完成！
echo ==============================
pause