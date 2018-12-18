%MACRO addseq(n);
%global seq;
proc sql inobs=&n noprint;
	select obs 
	into :seq separated by ','
	from repro.mapesum;
quit;
%MEnd;

%MACRO hdpara();
%do i=1 %to 24;
	%global hseq&i;
	%global dseq&i;
%end;
proc sql noprint;
	select h,d
	into :hseq1 - :hseq24 ,:dseq1 - :dseq24
	from repro.Paracv;
quit;
%MEnd;

%macro shift(h,d);
proc expand data=a&id out=a&id method=none;
id Date;
%do i=1 %to &h;
	convert tem = tem_lag&i / transformout = (lag &i);
%end;
%do i=1 %to &d;
	convert tem = tem_movave&i / transformout = (movave %eval(&i*24) trim %eval(&i*24-1));
%end;
run;
%mend;

%MACRO modifyinput(id,id2,h,d,hour);
*this function is required to pick items in seq1-id
add them up and average temperature.;
%addseq(&id);
%trainload(&id2);
%testload(&id2);
proc sql;
	create table a&id as
	select DHMS(MDY(month,day,year),hour,0,0) as Date ,year,month,day,hour,sum(tem)*1.0/&id as tem,(sum(tem)*1.0/&id)**2 as tem2,(sum(tem)*1.0/&id)**3 as tem3 from repro.temperature
	where station_id in (&seq)
	group by year,month,day,hour
	order by year,month,day,hour;
quit;	
%let mname = %STR(tem tem2 tem3 tem*month tem2*month tem3*month tem*hour tem2*hour tem3*hour);

%shift(&h,&d);

data lag_a&id;
	set a&id;
   %do n=1 %to &h;
	   tem_lag&n.s = tem_lag&n**2;
	   tem_lag&n.c = tem_lag&n**3;
	   %let mname = &mname tem_lag&n tem_lag&n.s tem_lag&n.c 
	   tem_lag&n*month tem_lag&n.s*month tem_lag&n.c*month
	   tem_lag&n*hour tem_lag&n.s*hour tem_lag&n.c*hour;
   %end;
   %do n=1 %to &d;
	   tem_movave&n.s = tem_movave&n**2;
	   tem_movave&n.c = tem_movave&n**3;
	   %let mname = &mname tem_movave&n tem_movave&n.s tem_movave&n.c 
	   tem_movave&n*month tem_movave&n.s*month tem_movave&n.c*month
	   tem_movave&n*hour tem_movave&n.s*hour tem_movave&n.c*hour;
   %end;

proc sql;	
	create table maintemperature&id as
	select monotonic() as trend,year,month,day,hour,weekday(mdy(month,day,year)) as weekday,
	* from lag_a&id;
	
	create table traintemperature&id as
	select * from maintemperature&id
	where year in (2005,2006);
	
	create table testtemperature&id as
	select * from maintemperature&id
	where year=2007;
quit;

%trainconcat(&id,&id2);
proc append base=insample&id&id2 data=testtemperature&id;
run;
*output: insample&id&id2;
%infittest(&id,&id2,&h,&d,&hour);

%MEND;
		
%MACRO trainconcat(id,id2);
data insample&id&id2;
set traintemperature&id;
set trainload&id2; *(firstobs = %eval(&d+1));
run;
%Mend;

%MACRO infittest(id1,id2,h,d,hour);

	data insample&id1&id2;
	set insample&id1&id2(drop=trend);
	run;
	proc sql;
	create table insample&id1&id2 as
	select monotonic() as trend,* from insample&id1&id2;
	quit;

	proc sql;
		create table pre&hour as
		select * from insample&id1&id2
		where hour = &hour;
	quit;
	proc glm data=pre&hour noprint;
		class hour weekday month;
		model load = trend hour weekday month hour*weekday &mname /SINGULAR=10e-10;
		output out=res predicted=ypre;
	quit;
	
	proc sql;
	create table testpre as
	select year,month,day,hour,ypre from res
	where hour=&hour and load=.;
	quit;
	%if not %sysfunc(exist(testcb)) %then %do;
	data testcb;
	set testpre;
	run;
	%end;
	%else %do;
	proc append base=testcb data=testpre;
	run;
	%end;
%Mend;

%MACRO loopAtest(zone);
	%global mname;
	%hdpara();
	%trainload(&zone);*name: trainload&id;
	%testload(&zone);*name: cvload&id;	
%do hour=1 %to 24;
	%modifyinput(11,&zone,&&&hseq&hour,&&&dseq&hour,&hour);
%end;
proc sql;
create table testcb as
select * from testcb
order by year,month,day,hour;
quit;
	proc sql;
		create table temp as
		select monotonic() as id,ypre from testcb;
	quit;
	proc sql;
		create table temp2 as
		select monotonic() as id,load from testload&zone;

		create table cb as
		select temp.ypre,temp2.load
		from temp,temp2
		where temp.id = temp2.id;
		
		create table MAPE as
		select distinct sum(abs((load-ypre))/load)/count(*)*100 as mape 
		from cb;

		select mape from MAPE;
	quit;
%Mend;

%MACRO trainload(id);
proc sql;
create table trainload&id as
	select year,sum(load) as load from repro.load
	where year in (2005,2006)
	group by year,month,day,hour;
quit;
%MEND;

%MACRO testload(id);
proc sql;
create table testload&id as
	select year,sum(load) as load from repro.load
	where year in (2007)
	group by year,month,day,hour;
quit;
%MEND;
