set thisPath (get-item $MyInvocation.MyCommand.Path).Directory.parent.FullName
cd (Join-Path $thisPath drivebuild)
& (Join-Path $thisPath drivebuild\venv\Scripts\Activate.ps1)

set commonPath (Join-Path $thisPath common)
set httpUtilityPath (Join-Path $thisPath httpUtility)
set pythonPath "$commonPath;$httpUtilityPath"
Set-Item -path env:PYTHONPATH -value ($pythonPath)

celery worker -A run_celery --loglevel=DEBUG
