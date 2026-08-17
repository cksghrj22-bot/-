#!/bin/bash
cd "$(dirname "$0")"
echo "════════════════════════════════════════"
echo " 멈춘 블로그 자동화 정리"
echo "════════════════════════════════════════"
pkill -f naver_blog_save 2>/dev/null && echo "· node 프로세스 종료" || echo "· 종료할 node 없음"
pkill -f blog_save_all 2>/dev/null
pkill -f "_naver_profile" 2>/dev/null && echo "· 크롬 자동화 종료" || echo "· 종료할 크롬 없음"
rm -f _naver_profile/.run.lock && echo "· 락 해제"
sleep 1
echo ""
echo "정리 끝. 이제 에세이2_임시저장.command 를 실행하세요."
echo ""
read -p "엔터 누르면 닫힘 " _
