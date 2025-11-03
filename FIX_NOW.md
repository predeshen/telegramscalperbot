# FIX YOUR SCANNERS NOW

## The Problem
Your scanners crash with: `python: command not found`

## The Solution
Run these 4 commands on your server:

```bash
cd ~/telegramscalperbot
git pull origin main
pip3 install openpyxl>=3.1.0
./stop_all_scanners.sh && ./start_all_scanners.sh --monitor
```

## That's It!

After running these commands:
- ✅ Scanners will use `python3` (not `python`)
- ✅ Excel reporting will work
- ✅ All 6 scanners will start successfully
- ✅ You'll receive email reports within 5 minutes

## If You Still Have Issues

Check if openpyxl is installed:
```bash
pip3 list | grep openpyxl
```

If not installed, run:
```bash
pip3 install openpyxl>=3.1.0
```

Then restart:
```bash
./stop_all_scanners.sh
./start_all_scanners.sh --monitor
```

---

**Just run the 4 commands above and your scanners will work!**
