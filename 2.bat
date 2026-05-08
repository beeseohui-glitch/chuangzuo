@echo off
chcp 65001 >nul
set OUTPUT=review_backend2.txt
if exist %OUTPUT% del %OUTPUT%

for %%f in (
models\agent_message.py
models\material_pack.py
crews\__init__.py
crews\xiaohongshu_crew.py
config\__init__.py
validators\__init__.py
validators\result_validator.py
) do (
if exist "%%f" (
echo ========== FILE: %%f ========== >> %OUTPUT%
type "%%f" >> %OUTPUT%
echo. >> %OUTPUT%
) else (
echo ========== FILE: %%f [NOT FOUND] ========== >> %OUTPUT%
)
)

echo Done: %OUTPUT%
