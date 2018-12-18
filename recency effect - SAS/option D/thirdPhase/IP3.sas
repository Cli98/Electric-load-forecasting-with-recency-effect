*libname repro 'W:\Desktop\recency effect';
*%include 'W:\Desktop\recency effect\thirdPhase\infittestModel.sas';
libname repro 'D:\recency effect\option D';
%include 'D:\recency effect\option D\thirdPhase\infittestModel.sas';
%loopAtest(21);


*testcb for comcat value of predict result;
%let zone=21;
