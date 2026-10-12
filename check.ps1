# Proverka dostupnosti servisov lokalnoy sredy PIS.
# Ispolzovanie: .\check.ps1 [host]   (po defaultu localhost)

param([string]$TargetHost = "localhost")
$H = $TargetHost
$FAIL = 0

function Check([string]$Name, [string]$Url) {
    try {
        Invoke-WebRequest -Uri $Url -TimeoutSec 5 -UseBasicParsing | Out-Null
        Write-Host "[OK]   $Name"
    } catch {
        Write-Host "[FAIL] $Name ($Url)"
        $script:FAIL = 1
    }
}

Write-Host "=== Proverka servisov na $H ==="
Check "Ollama (LLM)"          "http://${H}:11434/api/tags"
Check "Lab 1: MCP (Python)"   "http://${H}:8000/mcp"
Check "Lab 2: ADK A2A"        "http://${H}:8002/.well-known/agent-card.json"
Check "Lab 3: LangChain A2A"  "http://${H}:8003/.well-known/agent-card.json"
Check "Lab 4: Smolagents A2A" "http://${H}:8004/.well-known/agent-card.json"
Check "Lab 5: CrewAI A2A"     "http://${H}:8005/.well-known/agent-card.json"
Check "Lab 6: Strands A2A"    "http://${H}:8006/.well-known/agent-card.json"
Check "Lab 9: MCP (Go)"       "http://${H}:8100/mcp"
Check "Lab 10: A2UI"          "http://${H}:3000"
Write-Host "==============================="
if ($FAIL -eq 0) {
    Write-Host "Vse servisy dostupny."
} else {
    Write-Host "Est nedostupnye servisy (zapustite nuzhnye profily v docker-compose.local.yaml)."
}
exit $FAIL
