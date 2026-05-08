@echo off
chcp 65001 >nul
set OUTPUT=review_prompts.txt
if exist %OUTPUT% del %OUTPUT%

for %%f in (prompts\*.md) do (
echo ========== FILE: %%f ========== >> %OUTPUT%
type "%%f" >> %OUTPUT%
echo. >> %OUTPUT%
)

echo Done: %OUTPUT%
