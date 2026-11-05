# FnGuide 리포트 → Google Drive 자동 저장

평일 오전 8시마다 FnGuide에 로그인해 **전 영업일 이후 발간된 신규 리포트**를 PDF로 받아
Google Drive `주식전략` 폴더에 저장합니다. 월요일에 실행하면 금요일 발간분부터 받습니다.

## 1. 설치 (최초 1회)
1. Python 3.10 이상, [Google Drive for desktop](https://www.google.com/drive/download/) 설치 및 로그인
2. 이 폴더에서 아래를 실행합니다.
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
3. `.env.example`을 복사해 `.env`를 만들고 ID/PW, `SAVE_DIR`(드라이브의 `주식전략` 폴더 경로)를 채웁니다.

## 2. 화면 구조 맞추기 (최초 1회)
```bash
python fnguide_download.py --inspect
```
- 브라우저가 열리고 로그인됩니다. 리포트 목록으로 이동한 뒤 Enter를 누르세요.
- 목록 화면의 주소창 URL을 `.env`의 `LIST_URL`에 넣습니다.
- 한 번 더 `--inspect`를 실행하면 `debug/` 폴더에 목록과 새 창 화면이 저장됩니다.
- `python fnguide_download.py --dry-run`으로 받을 목록이 맞게 나오는지 확인합니다.
  목록이 맞지 않으면 `debug/` 파일을 보고 `.env`의 셀렉터를 조정합니다.

## 3. 매일 자동 실행 (Windows 작업 스케줄러)
명령 프롬프트에서 실행합니다. 경로는 실제 폴더 위치로 바꾸세요.
```bat
schtasks /create /tn "FnGuide리포트" /tr "C:\경로\fnguide_downloader\run_daily.bat" /sc weekly /d MON,TUE,WED,THU,FRI /st 08:00
```
실행 기록은 `run.log`에 남습니다. 이미 받은 리포트는 `history.json`으로 걸러져 다시 받지 않습니다.
