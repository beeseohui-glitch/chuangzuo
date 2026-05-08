@echo off
chcp 65001 >nul
set OUTPUT=review_frontend.txt
if exist %OUTPUT% del %OUTPUT%

for %%f in (
frontend\src\app\create\page.tsx
frontend\src\stores\create-store.ts
frontend\src\lib\api.ts
frontend\src\components\create\step-input.tsx
frontend\src\components\create\step-topic.tsx
frontend\src\components\create\step-title.tsx
frontend\src\components\create\step-article.tsx
frontend\src\components\create\step-output.tsx
frontend\src\components\shared\agent-status.tsx
frontend\src\types\index.ts
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
