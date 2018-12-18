libname repro 'D:\recency effect\option D';
%include 'D:\recency effect\option D\secondPhase\infitcvModel.sas';

%loopAcv(21,3,2);


proc iml;
start getminind(h,d);
   use Cvmapesum_0_2 ;
   read all var {mape} into array[colname=varNames];
   MA = shape(array,h+1,d+1);
   minval = min(MA);
	hind = 0;
	dind = 0;
   do i=1 to h+1;
   do j=1 to d+1;
	   	if MA[i,j] = minval[1] then do;
			hind = i;
			dind = j;
	end;
	end;
	end;
	ret = j(1,2, .);
	ret[1,1] = hind;
	ret[1,2] = dind;
   create ind from ret;
	append from ret;
	close ind;
finish;

call getminind(1,7);

/*
%let id=11;
%let id2=21;
%let h1=3;
%let d=2;
%let zone=21;
*/
