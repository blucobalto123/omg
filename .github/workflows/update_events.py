name: Update Ita and Events

on:
  schedule:
    - cron: "0 */3 * * *" # ogni 3 ore
  workflow_dispatch:

jobs:
  update-files:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository (no history)
        uses: actions/checkout@v3
        with:
          fetch-depth: 1

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'

      - name: Install dependencies
        run: |
          python -m pip install requests pytz
          pip install bs4
          pip install chardet
          
      - name: Run EPG grabber script
        env:
          M3U4U_EPG: ${{ secrets.M3U4U_EPG }}
        run: |
          rm -f daddyliveSchedule.json
          rm -f 247channels.html
          python onlyevents.py
          python itaevents.py
          
      - name: Force commit and push the changes (no history)
        run: |
          git config --global user.name "actions-user"
          git config --global user.email "actions@github.com"
          git add .
          git commit -m "Update Ita and Events 3h"
          git push --force
