set -ex

rm -f txt/BUFRCREX_CodeFlag_en.txt | true
cat BUFRCREX_CodeFlag_en_*.csv >> txt/BUFRCREX_CodeFlag_en.txt

rm -f txt/BUFRCREX_TableB_en.txt | true
cat BUFRCREX_TableB_en_*.csv >> txt/BUFRCREX_TableB_en.txt

cp BUFR_TableA_en.csv txt/BUFR_TableA_en.txt
cp BUFR_TableC_en.csv txt/BUFR_TableC_en.txt

rm -f txt/BUFR_TableD_en.txt | true
cat BUFR_TableD_en_*.csv >> txt/BUFR_TableD_en.txt

cp CREX_TableA_en.csv txt/CREX_TableA_en.txt
cp CREX_TableC_en.csv txt/CREX_TableC_en.txt

rm -f txt/CREX_TableD_en.txt | true
cat CREX_TableD_en_*.csv >> txt/CREX_TableD_en.txt

python3 scripts/csv2xml.py
