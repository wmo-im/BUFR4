set -ex

# Concatenate CSV files (keeping only the first header) and drop the leading
# ID column from any file whose header starts with "ID", so the legacy txt
# output does not include it.
concat_no_id() {
  awk -v BINMODE=3 'FNR == 1 { strip = ($0 ~ /^"?ID"?,/) }
       (NR == 1) || (FNR > 1) { if (strip) sub(/^[^,]*,/, ""); print }' "$@"
}

rm -f txt/BUFRCREX_CodeFlag_en.txt | true
concat_no_id BUFRCREX_CodeFlag_en_*.csv > txt/BUFRCREX_CodeFlag_en.txt

rm -f txt/BUFRCREX_TableB_en.txt | true
concat_no_id BUFRCREX_TableB_en_*.csv > txt/BUFRCREX_TableB_en.txt

concat_no_id BUFR_TableA_en.csv > txt/BUFR_TableA_en.txt
concat_no_id BUFR_TableC_en.csv > txt/BUFR_TableC_en.txt

rm -f txt/BUFR_TableD_en.txt | true
concat_no_id BUFR_TableD_en_*.csv > txt/BUFR_TableD_en.txt

concat_no_id CREX_TableA_en.csv > txt/CREX_TableA_en.txt
concat_no_id CREX_TableC_en.csv > txt/CREX_TableC_en.txt

rm -f txt/CREX_TableD_en.txt | true
concat_no_id CREX_TableD_en_*.csv > txt/CREX_TableD_en.txt

python3 scripts/csv2xml.py
