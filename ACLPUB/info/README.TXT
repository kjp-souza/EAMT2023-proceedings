# Reading the page numbers from the Proceedings TOC

cat EAMT2020-proceedings.toc| grep "\\contentsline {section}" | awk -F'}{' '{print $3, "%", $2}' > submissions_pages.txt

