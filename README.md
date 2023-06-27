# Proceedings of the EAMT 2023 
[EAMT 2023](https://events.tuni.fi/eamt23/) - 22nd Annual Conference of the European Association for Machine Translation



## Information required

Current TEX file assumes that papers are available in PDF format, and that the following directories exist

    misc
    papers_implement
    papers_prodproj
    papers_restech
    papers_restrans

It also assumes that papers to be included in it are reviewed `.pdf` files with blank Footer area and page number, since the `.tex` proceedings code contains its own footer & page numbering that are going to be automatically added to all papers on the first sheet. This if to avoid data overlap.

The following LaTex code snippets were also deactivated (or commented with the '%' sign) so it will stop creating new odd blank pages. 
If you wish to have new odd blank pages to separate your proceedings chapters, simply activate them again by removing the '%' sign from the beginning where necessary in the code.

`%\newcommand{\newoddpage} {\clearpage`  
`%  \ifthenelse{\isodd{\value{page}}}{}`  
`%  {\thispagestyle{empty}\quad\newpage}}`  

and 

`%  \newoddpage`
    
## ACL Anthology
 
The proceedings and all the corresponding papers are also available into the ACL Anthology. 

Peer-reviewing was done using EasyChair, so proceedings were adapted to the ACLPUB format following the import instructions avaliable [here](https://www.aclweb.org/anthology/info/contrib/). The `ACLPUB` directory contains the followed procedure. 

The script `easy2acl.py`, available at https://github.com/acl-org/easy2acl, was adapted to our needs.
