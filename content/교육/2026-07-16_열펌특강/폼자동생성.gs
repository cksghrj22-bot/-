/**
 * 열펌 워드월 — 구글폼 자동 생성 스크립트 (Apps Script)
 *
 * 사용법 (1분):
 *   1. script.google.com 접속 (구글 로그인 상태에서)
 *   2. 「새 프로젝트」 → 편집기에 이 파일 내용 전체 붙여넣기 (기존 내용 지우고)
 *   3. 위쪽 「실행 ▶」 클릭 → 권한 요청 뜨면 [권한 검토 → 계정 선택 → 허용]
 *   4. 아래 「실행 로그」에 뜨는 링크 2개를 열펌_워드월.html 첫 화면에 붙여넣기
 *
 * 하는 일: 폼 생성 + 질문 2개 + 응답 시트 연결 + 시트 '링크 뷰어' 공유까지 전부 자동.
 */
function 열펌폼만들기() {
  // 1) 폼 + 질문 2개
  const form = FormApp.create('열펌이란?');
  form.addTextItem()
      .setTitle('열펌이란 ______다. 한 단어로!')
      .setRequired(true);
  form.addParagraphTextItem()
      .setTitle('열펌에서 제일 궁금한 것 or 실패했던 경험 하나 (선택)');

  // 2) 응답 스프레드시트 만들고 연결
  const ss = SpreadsheetApp.create('열펌 워드월 응답');
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  // 3) 워드월이 첫 시트를 읽으므로, 빈 기본 시트는 지우고 응답 시트만 남긴다
  const fresh = SpreadsheetApp.openById(ss.getId());
  const sheets = fresh.getSheets();
  if (sheets.length > 1) {
    sheets.forEach(function (sh) {
      if (sh.getFormUrl() === null) fresh.deleteSheet(sh);
    });
  }

  // 4) 시트 공유: 링크가 있는 모든 사용자 = 뷰어 (워드월이 읽기 위한 필수 설정)
  DriveApp.getFileById(ss.getId())
      .setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);

  // 5) 링크 2개 출력
  const shortUrl = form.shortenFormUrl(form.getPublishedUrl());
  Logger.log('================================================');
  Logger.log('① 폼 링크 (워드월 첫째 칸): ' + shortUrl);
  Logger.log('② 시트 링크 (워드월 둘째 칸): ' + fresh.getUrl());
  Logger.log('================================================');
  Logger.log('이 두 줄을 열펌_워드월.html 첫 화면에 붙여넣고 [▶ 워드월 시작]');
}
