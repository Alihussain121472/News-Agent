$url = "https://novabrief-web.onrender.com/api/temp/send-welcome?email=syedali6160@gmail.com"
for ($i=0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 30
    try {
        $result = Invoke-RestMethod -Uri $url -Method Get -ErrorAction Stop
        if ($result -match "Sent successfully") {
            echo "Success! Reverting code..."
            git reset --hard HEAD~1
            git push origin main --force
            git push origin main:render-role-dashboards --force
            exit 0
        }
    } catch {
        echo "Not ready yet..."
    }
}
